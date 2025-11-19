"""URL normalization utilities"""
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
import re


def normalize_url(url: str) -> str:
    """
    Normalize URL for deduplication:
    - Convert to lowercase
    - Remove tracking parameters
    - Remove fragments
    - Standardize www
    - Remove trailing slash
    """
    url = url.strip()
    
    # Parse URL
    parsed = urlparse(url)
    
    # Normalize scheme
    scheme = parsed.scheme.lower() if parsed.scheme else 'https'
    
    # Normalize domain (remove www, convert to lowercase)
    netloc = parsed.netloc.lower()
    if netloc.startswith('www.'):
        netloc = netloc[4:]
    
    # Remove common tracking parameters
    tracking_params = {
        'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
        'fbclid', 'gclid', 'msclkid', 'mc_cid', 'mc_eid',
        '_ga', '_gl', 'ref', 'source'
    }
    
    query_params = parse_qs(parsed.query)
    filtered_params = {k: v for k, v in query_params.items() if k not in tracking_params}
    query = urlencode(filtered_params, doseq=True) if filtered_params else ''
    
    # Remove fragment
    fragment = ''
    
    # Remove trailing slash from path
    path = parsed.path.rstrip('/') if parsed.path != '/' else parsed.path
    
    # Reconstruct URL
    normalized = urlunparse((scheme, netloc, path, parsed.params, query, fragment))
    
    return normalized


def is_valid_url(url: str) -> bool:
    """Check if URL is valid"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False


def extract_domain(url: str) -> str:
    """Extract domain from URL"""
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower().replace('www.', '')
    except:
        return ''
