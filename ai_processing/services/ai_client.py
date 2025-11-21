"""
OpenAI-compatible API Client
"""

import json
import time
from typing import Dict, List, Optional, Any
import requests


class AIClient:
    """
    Client for OpenAI-compatible API
    Supports chat completions and function calling
    """
    
    def __init__(
        self,
        api_url: str,
        api_key: str,
        model: str,
        timeout: int = 30,
        max_retries: int = 3
    ):
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Ensure URL ends with /chat/completions
        if not self.api_url.endswith("/chat/completions"):
            self.api_url = f"{self.api_url}/chat/completions"
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        functions: Optional[List[Dict]] = None,
        function_call: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send chat completion request
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            functions: Function definitions for function calling
            function_call: Force specific function call
        
        Returns:
            API response dict
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            # OpenRouter requires a referer or title; provide both
            "HTTP-Referer": "https://eternalgyn-rewriter.local",
            "X-Title": "Eternalgy-News-Rewriter"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "n": 1
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        if functions:
            payload["functions"] = functions
        
        if function_call:
            payload["function_call"] = function_call
        
        # Retry logic
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    self.api_url,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                )
                if response.status_code != 200:
                    # Capture error body for debugging
                    try:
                        err_text = response.text
                    except Exception:
                        err_text = ""
                    raise Exception(f"API request failed: {response.status_code} {err_text}")
                return response.json()

            except requests.exceptions.RequestException as e:
                if attempt == self.max_retries - 1:
                    raise Exception(f"API request failed after {self.max_retries} retries: {e}")
                
                # Exponential backoff
                wait_time = 2 ** attempt
                time.sleep(wait_time)
        
        raise Exception("Unexpected error in API request")
    
    def extract_content(self, response: Dict) -> str:
        """Extract text content from API response"""
        try:
            return response["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            raise Exception(f"Failed to extract content from response: {e}")
    
    def extract_function_call(self, response: Dict) -> Optional[Dict]:
        """Extract function call from API response"""
        try:
            message = response["choices"][0]["message"]
            if "function_call" in message:
                return {
                    "name": message["function_call"]["name"],
                    "arguments": json.loads(message["function_call"]["arguments"])
                }
            return None
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            raise Exception(f"Failed to extract function call: {e}")

    def chat_completion_with_functions(
        self,
        messages: List[Dict[str, str]],
        functions: List[Dict],
        function_call: Optional[Dict] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Send chat completion request with function calling
        
        Args:
            messages: List of message dicts
            functions: List of function schemas
            function_call: Force specific function (e.g., {"name": "function_name"})
            temperature: Sampling temperature
            max_tokens: Maximum tokens
        
        Returns:
            API response dict
        """
        return self.chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            functions=functions,
            function_call=function_call
        )
    
    def extract_function_arguments(self, response: Dict) -> Optional[Dict]:
        """
        Extract function call arguments from API response
        
        Args:
            response: API response dict
        
        Returns:
            Function arguments as dict, or None if no function call
        """
        try:
            message = response["choices"][0]["message"]
            
            # Check for function_call (OpenAI format)
            if "function_call" in message:
                args_str = message["function_call"]["arguments"]
                if isinstance(args_str, str):
                    return json.loads(args_str)
                return args_str
            
            # Check for tool_calls (newer format)
            if "tool_calls" in message and message["tool_calls"]:
                args_str = message["tool_calls"][0]["function"]["arguments"]
                if isinstance(args_str, str):
                    return json.loads(args_str)
                return args_str
            
            return None
            
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            print(f"Warning: Failed to extract function arguments: {e}")
            return None
