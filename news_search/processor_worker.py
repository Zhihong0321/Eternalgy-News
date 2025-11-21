"""Processing worker for discovered news links"""
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict
from .database import Database
from .url_normalizer import extract_domain
from .config import (
    SAME_DOMAIN_DELAY,
    MAX_CONCURRENT_DOMAINS,
    REQUEST_TIMEOUT,
    MAX_RETRIES
)


class ProcessorWorker:
    def __init__(self, ai_processor=None):
        """
        Initialize processor worker
        
        Args:
            ai_processor: Your AI processing module (Jina Reader + translator)
                         Should have a process(url) method that returns processed content
        """
        self.db = Database()
        self.ai_processor = ai_processor
        self.domain_last_request = {}  # Track last request time per domain
    
    def process_pending_links(self, limit: int = 100) -> Dict:
        """
        Process pending news links with domain-aware rate limiting
        
        Args:
            limit: Maximum number of links to process
        
        Returns:
            Dictionary with processing statistics
        """
        print(f"Fetching up to {limit} pending links...")
        pending_links = self.db.get_pending_links(limit)
        
        if not pending_links:
            print("No pending links to process")
            return {
                "total": 0,
                "success": 0,
                "failed": 0,
                "skipped": 0
            }
        
        print(f"Found {len(pending_links)} pending links")
        
        # Group links by domain
        domain_groups = self._group_by_domain(pending_links)
        
        print(f"Grouped into {len(domain_groups)} domains")
        for domain, links in domain_groups.items():
            print(f"  {domain}: {len(links)} links")
        
        # Process domains concurrently
        results = self._process_domains(domain_groups)
        
        return results
    
    def _group_by_domain(self, links: List[Dict]) -> Dict[str, List[Dict]]:
        """Group links by domain"""
        groups = defaultdict(list)
        for link in links:
            domain = extract_domain(link['url'])
            groups[domain].append(link)
        return dict(groups)
    
    def _process_domains(self, domain_groups: Dict[str, List[Dict]]) -> Dict:
        """Process multiple domains concurrently"""
        stats = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "skipped": 0,
            "by_domain": {}
        }
        
        with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_DOMAINS) as executor:
            # Submit each domain for processing
            future_to_domain = {
                executor.submit(self._process_domain, domain, links): domain
                for domain, links in domain_groups.items()
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_domain):
                domain = future_to_domain[future]
                try:
                    domain_stats = future.result()
                    stats["by_domain"][domain] = domain_stats
                    stats["total"] += domain_stats["total"]
                    stats["success"] += domain_stats["success"]
                    stats["failed"] += domain_stats["failed"]
                    stats["skipped"] += domain_stats["skipped"]
                except Exception as e:
                    print(f"Error processing domain {domain}: {e}")
        
        return stats
    
    def _process_domain(self, domain: str, links: List[Dict]) -> Dict:
        """Process all links from a single domain with rate limiting"""
        print(f"\n[{domain}] Processing {len(links)} links...")
        
        stats = {
            "total": len(links),
            "success": 0,
            "failed": 0,
            "skipped": 0
        }
        
        for i, link in enumerate(links, 1):
            # Apply rate limiting for same domain
            self._apply_rate_limit(domain)
            
            print(f"[{domain}] ({i}/{len(links)}) Processing: {link['url']}")
            
            if self.db.is_domain_blacklisted(domain):
                print(f"[{domain}] ⚠️ Domain is blacklisted, skipping link.")
                self.db.update_link_status(link['id'], 'blocked', 'Domain blacklisted')
                stats["skipped"] += 1
                continue

            # Update status to processing
            self.db.update_link_status(link['id'], 'processing')
            
            # Process the link
            status = self._process_single_link(link)
            
            if status == "success":
                stats["success"] += 1
                print(f"[{domain}] ✓ Success")
            elif status == "blocked":
                stats["skipped"] += 1
                print(f"[{domain}] ⚠️ Blocked by Jina")
            else:
                stats["failed"] += 1
                print(f"[{domain}] ✗ Failed")
        
        print(f"[{domain}] Completed: {stats['success']} success, {stats['failed']} failed")
        return stats
    
    def _apply_rate_limit(self, domain: str):
        """Apply rate limiting for domain"""
        if domain in self.domain_last_request:
            elapsed = time.time() - self.domain_last_request[domain]
            if elapsed < SAME_DOMAIN_DELAY:
                sleep_time = SAME_DOMAIN_DELAY - elapsed
                print(f"  [Rate limit] Waiting {sleep_time:.1f}s for {domain}...")
                time.sleep(sleep_time)
        
        self.domain_last_request[domain] = time.time()
    
    def _process_single_link(self, link: Dict) -> str:
        """
        Process a single link with retry logic
        
        Args:
            link: Link dictionary with id, url, etc.
        
        Returns:
            "success", "blocked", or "failed"
        """
        url = link['url']
        link_id = link['id']
        
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                if self.ai_processor:
                    title = link.get('title', '')
                    result = self.ai_processor.process(url, title=title)
                    
                    if result:
                        if result.get('blocked'):
                            self._handle_blacklisted_link(link, result)
                            return "blocked"

                        if result.get('success'):
                            self.db.save_processed_content(
                                link_id=link_id,
                                title=result.get('title'),
                                title_en=result.get('title_en'),
                                title_zh=result.get('title_zh'),
                                title_ms=result.get('title_ms'),
                                content=result.get('content'),
                                translated_content=result.get('translated_content'),
                                tags=result.get('tags'),
                                country=result.get('country'),
                                news_date=result.get('news_date'),
                                metadata=result.get('metadata')
                            )
                            
                            self.db.update_link_status(link_id, 'completed')
                            return "success"
                        else:
                            error_msg = result.get('error', 'Unknown error')
                            print(f"  Attempt {attempt}/{MAX_RETRIES}: Processing failed - {error_msg}")
                    else:
                        print(f"  Attempt {attempt}/{MAX_RETRIES}: Processing returned None")
                else:
                    print(f"  [Mock] Processing {url}")
                    time.sleep(0.5)
                    self.db.update_link_status(link_id, 'completed')
                    return "success"
                    
            except Exception as e:
                print(f"  Attempt {attempt}/{MAX_RETRIES}: Error - {str(e)}")
        
        self.db.update_link_status(link_id, 'failed', 'Max retries exceeded')
        return "failed"

    def _handle_blacklisted_link(self, link: Dict, result: Dict):
        '''Record the blocked link/domain and update status.'''
        url = link['url']
        domain = extract_domain(url)
        reason = result.get('block_reason') or result.get('metadata', {}).get('block_reason', 'Jina Reader blocked')
        title = link.get('title') or self._title_from_url(url)
        self.db.add_blacklisted_site(domain, url, title, reason)
        self.db.update_link_status(link['id'], 'blocked', reason)

    def _title_from_url(self, url: str) -> str:
        '''Derive a simple title from the URL for logging.'''
        from urllib.parse import urlparse, unquote
        parsed = urlparse(url)
        segments = [seg for seg in parsed.path.split('/') if seg]
        candidate = segments[-1] if segments else parsed.netloc
        candidate = candidate.replace('-', ' ').replace('_', ' ')
        return unquote(candidate)
    def process_specific_links(self, link_ids: List[int]) -> Dict:
        """Process specific links by ID"""
        links = self.db.get_links_by_ids(link_ids)
        
        if not links:
            return {
                "total": 0,
                "success": 0,
                "failed": 0,
                "skipped": 0
            }
        
        domain_groups = self._group_by_domain(links)
        return self._process_domains(domain_groups)
