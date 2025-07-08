import json
import requests
import re
import time
import logging
from typing import List, Dict, Optional
import os

logger = logging.getLogger(__name__)

class GroqClient:
    """Client for interacting with the Groq API for IOC extraction."""
    
    def __init__(self, api_key: Optional[str] = None, config: dict = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("Groq API key not provided. Set GROQ_API_KEY environment variable.")
        
        if config is None:
            raise ValueError("Config dictionary must be provided")
            
        self.base_url = config["groq"]["api_url"]
        self.model = config["groq"]["model"]
        self.temperature = config["groq"].get("temperature", 0.1)
        self.max_retries = config["groq"].get("max_retries", 3)
        self.retry_delay = config["groq"].get("retry_delay", 1)
        
        self.system_prompt = (
            config["prompts"]["ioc_extraction"]
            + "\n\nIMPORTANT: Respond ONLY with a JSON array of objects, no explanation, no markdown, no notes, no code block, no commentary."
        )
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def extract_iocs(self, text: str) -> List[Dict[str, str]]:
        """Extract IOCs from text using Groq's LLM with retry logic and better error handling."""
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Attempting IOC extraction (attempt {attempt + 1}/{self.max_retries})")
                
                response = requests.post(
                    self.base_url,
                    headers=self.headers,
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": self.system_prompt},
                            {"role": "user", "content": f"Extract IOCs from this text: {text}"}
                        ],
                        "temperature": self.temperature
                    },
                    timeout=30
                )
                response.raise_for_status()
                
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                usage = result.get("usage", {})
                
                logger.info(f"API usage: {json.dumps(usage, indent=2)}")
                logger.debug(f"Raw LLM response: {content}")
                
                # Parse JSON response with enhanced error handling
                iocs = self._parse_json_response(content)
                logger.info(f"Extracted {len(iocs)} IOCs")
                return iocs
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"API request failed (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                else:
                    logger.error("All retry attempts failed")
                    return []
            except Exception as e:
                logger.error(f"Unexpected error during IOC extraction: {e}")
                return []
        
        return []

    def _parse_json_response(self, content: str) -> List[Dict[str, str]]:
        """Parse JSON response with multiple fallback strategies."""
        # Strategy 1: Direct JSON parse
        try:
            data = json.loads(content)
            if isinstance(data, list):
                return self._validate_ioc_data(data)
        except json.JSONDecodeError:
            pass
        
        # Strategy 2: Extract JSON array from text
        json_pattern = r'\[\s*\{.*?\}\s*\]'
        match = re.search(json_pattern, content, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(0))
                return self._validate_ioc_data(data)
            except json.JSONDecodeError:
                pass
        
        # Strategy 3: Extract individual JSON objects
        object_pattern = r'\{[^{}]*"ioc"[^{}]*\}'
        objects = re.findall(object_pattern, content)
        iocs = []
        for obj_str in objects:
            try:
                obj = json.loads(obj_str)
                if self._is_valid_ioc(obj):
                    iocs.append(obj)
            except json.JSONDecodeError:
                continue
        
        if iocs:
            return iocs
        
        logger.warning("Could not extract valid JSON from LLM response")
        return []

    def _validate_ioc_data(self, data: List[Dict]) -> List[Dict[str, str]]:
        """Validate and clean IOC data."""
        validated = []
        for item in data:
            if self._is_valid_ioc(item):
                # Normalize the IOC
                normalized_ioc = self._normalize_ioc(item["ioc"])
                validated.append({
                    "ioc": normalized_ioc,
                    "type": item["type"]
                })
        return validated

    def _is_valid_ioc(self, item: Dict) -> bool:
        """Check if an IOC object is valid."""
        return (
            isinstance(item, dict) and
            "ioc" in item and
            "type" in item and
            isinstance(item["ioc"], str) and
            isinstance(item["type"], str) and
            item["ioc"].strip() and
            item["type"].strip()
        )

    def _normalize_ioc(self, ioc: str) -> str:
        """Normalize obfuscated IOCs."""
        # Common obfuscation patterns
        normalizations = {
            "hxxp": "http",
            "hxxps": "https",
            "[.]": ".",
            "[@]": "@",
            "[:]": ":",
            "(//)": "//",
        }
        
        normalized = ioc
        for obfuscated, normal in normalizations.items():
            normalized = normalized.replace(obfuscated, normal)
        
        return normalized.strip()
