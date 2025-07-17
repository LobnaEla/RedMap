import json
import re
import time
import logging
from typing import List, Dict, Optional
import os
from openai import OpenAI

logger = logging.getLogger(__name__)

class LLMClient:
    """Unified client for interacting with LLM APIs (Groq, OpenAI, OpenRouter) for IOC extraction."""
    
    def __init__(self, api_key: Optional[str] = None, config: Optional[dict] = None):
        if config is None:
            raise ValueError("Config dictionary must be provided")
            
        self.config = config
        self.llm_config = config["llm"]
        self.provider = self.llm_config["provider"]
        
        # Get provider-specific configuration
        provider_config = self.llm_config[self.provider]
        
        # Get API key
        api_key_env = provider_config["api_key_env"]
        self.api_key = api_key or os.getenv(api_key_env)
        if not self.api_key:
            raise ValueError(f"API key not provided. Set {api_key_env} environment variable.")
        
        # Set up OpenAI client with provider-specific settings
        self.base_url = provider_config["base_url"]
        self.model = provider_config["model"]
        self.temperature = self.llm_config.get("temperature", 0.1)
        self.max_retries = self.llm_config.get("max_retries", 3)
        self.retry_delay = self.llm_config.get("retry_delay", 1)
        
        # Initialize OpenAI client
        client_kwargs = {
            "api_key": self.api_key,
            "base_url": self.base_url
        }
        
        self.client = OpenAI(**client_kwargs)
        
        # Set up extra headers for OpenRouter
        self.extra_headers = {}
        if self.provider == "openrouter" and "extra_headers" in provider_config:
            self.extra_headers = provider_config["extra_headers"]
        
        self.system_prompt = (
            config["prompts"]["ioc_extraction"]
            + "\n\nIMPORTANT: Respond ONLY with a JSON array of objects, no explanation, no markdown, no notes, no code block, no commentary."
        )
        
        logger.info(f"Initialized LLMClient with provider: {self.provider}, model: {self.model}")

    def extract_iocs(self, text: str) -> List[Dict[str, str]]:
        """Extract IOCs from text using the configured LLM with retry logic and better error handling."""
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Attempting IOC extraction (attempt {attempt + 1}/{self.max_retries})")
                
                # Prepare messages
                messages = [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"Extract IOCs from this text: {text}"}
                ]
                
                # Prepare request parameters
                request_params = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": self.temperature
                }
                
                # Add extra headers if using OpenRouter
                if self.extra_headers:
                    response = self.client.chat.completions.create(
                        extra_headers=self.extra_headers,
                        **request_params
                    )
                else:
                    response = self.client.chat.completions.create(**request_params)
                
                content = response.choices[0].message.content
                
                # Log usage information if available
                if hasattr(response, 'usage') and response.usage:
                    usage = {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens
                    }
                    logger.info(f"API usage: {json.dumps(usage, indent=2)}")
                
                logger.debug(f"Raw LLM response: {content}")
                
                # Parse JSON response with enhanced error handling
                iocs = self._parse_json_response(content)
                logger.info(f"Extracted {len(iocs)} IOCs")
                return iocs
                
            except Exception as e:
                logger.warning(f"API request failed (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                else:
                    logger.error("All retry attempts failed")
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
            bool(item["ioc"].strip()) and
            bool(item["type"].strip())
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
