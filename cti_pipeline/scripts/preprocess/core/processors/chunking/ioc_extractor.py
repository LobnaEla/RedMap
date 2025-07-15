"""
IOC Extractor Module

This module provides IOC extraction functionality using both LLM and regex approaches.
"""

import json
import requests
import re
import time
from typing import List, Dict
from .config import ChunkingConfig

class IOCExtractor:
    """IOC extraction using LLM and regex fallback"""
    
    # Regex patterns for different IOC types
    REGEX_PATTERNS = {
        'ipv4': r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
        'ipv6': r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b',
        'domain': r'\b[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*\.[a-zA-Z]{2,}\b',
        'url': r'https?://[^\s<>"{}|\\^`\[\]]+',
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'md5': r'\b[a-fA-F0-9]{32}\b',
        'sha1': r'\b[a-fA-F0-9]{40}\b',
        'sha256': r'\b[a-fA-F0-9]{64}\b',
        'sha512': r'\b[a-fA-F0-9]{128}\b',
        'cve': r'CVE-\d{4}-\d{4,}',
        'mitre_technique': r'T\d{4}(\.\d{3})?',
        'bitcoin': r'\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b',
    }
    
    def __init__(self, config: ChunkingConfig):
        self.config = config
        self.headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
        } if config.api_key else None
        
        # System prompt for LLM extraction
        self.system_prompt = """You are a cybersecurity analyst specializing in IOC extraction.
Analyze the provided text and extract all Indicators of Compromise (IOCs).
Return the results in a JSON array, where each object includes:
{
  "ioc": "<indicator_value>",
  "type": "<indicator_type>"
}

Include, but do not limit to, the following types:
- Network-based: IP addresses, domains, URLs, email addresses
- Host-based: file paths, filenames, file extensions, process names, registry keys
- File-related: file hashes (MD5, SHA-1, SHA-256, SHA-512)
- Email-related: email addresses, email subjects, malicious attachment names
- Cryptocurrency: Bitcoin addresses, Ethereum addresses, wallet IDs
- TTPs: MITRE ATT&CK technique IDs (T####.###)
- CVE: CVE identifiers (CVE-YYYY-####)

Normalize any obfuscated indicators (e.g., hxxp → http, [.] → ., [@] → @).
Do not include duplicates. Only extract IOCs that are explicitly mentioned.
Focus on actionable indicators that can be used for threat hunting.

IMPORTANT: Respond ONLY with a JSON array of objects, no explanation, no markdown, no notes, no code block, no commentary."""
    
    def extract_iocs(self, text: str) -> List[Dict[str, str]]:
        """Extract IOCs from text using LLM with regex fallback"""
        start_time = time.time()
        
        try:
            # Try LLM extraction first if enabled and API key is available
            if self.config.use_llm_extraction and self.config.api_key:
                print("[Chunker: ioc extractor] Attempting LLM-based IOC extraction")
                iocs = self._extract_with_llm(text)
                if iocs:
                    print(f"[Chunker: ioc extractor] LLM extraction found {len(iocs)} IOCs in {time.time() - start_time:.3f}s")
                    return iocs
                else:
                    print("[Chunker: ioc extractor] LLM extraction failed or returned no results")
            
            # Fallback to regex extraction
            if self.config.fallback_to_regex:
                print("[Chunker: ioc extractor] Using regex-based IOC extraction")
                iocs = self._extract_with_regex(text)
                print(f"[Chunker: ioc extractor] Regex extraction found {len(iocs)} IOCs in {time.time() - start_time:.3f}s")
                return iocs
            
            print("[Chunker: ioc extractor] No IOC extraction method available")
            return []
            
        except Exception as e:
            print(f"[Chunker: ioc extractor] IOC extraction failed: {e}")
            return []
    
    def _extract_with_llm(self, text: str) -> List[Dict[str, str]]:
        """Extract IOCs using LLM API"""
        if not self.headers:
            return []
        
        for attempt in range(self.config.max_retries):
            try:
                print(f"[Chunker: ioc extractor] LLM extraction attempt {attempt + 1}/{self.config.max_retries}")
                
                response = requests.post(
                    self.config.api_url,
                    headers=self.headers,
                    json={
                        "model": self.config.model,
                        "messages": [
                            {"role": "system", "content": self.system_prompt},
                            {"role": "user", "content": f"Extract IOCs from this text: {text}"}
                        ],
                        "temperature": self.config.temperature
                    },
                    timeout=30
                )
                response.raise_for_status()
                
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                
                # Parse JSON response
                iocs = self._parse_json_response(content)
                return self._validate_and_normalize_iocs(iocs)
                
            except requests.exceptions.RequestException as e:
                print(f"[Chunker: ioc extractor] LLM API request failed (attempt {attempt + 1}): {e}")
                if attempt < self.config.max_retries - 1:
                    time.sleep(self.config.retry_delay * (attempt + 1))
                    continue
                else:
                    print("[Chunker: ioc extractor] All LLM extraction attempts failed")
                    return []
            except Exception as e:
                print(f"[Chunker: ioc extractor] Unexpected error in LLM extraction: {e}")
                return []
        
        return []
    
    def _extract_with_regex(self, text: str) -> List[Dict[str, str]]:
        """Extract IOCs using regex patterns"""
        iocs = []
        seen = set()
        
        for ioc_type, pattern in self.REGEX_PATTERNS.items():
            if ioc_type in self.config.ioc_types:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    # Handle tuple matches (like from IPv6 pattern)
                    if isinstance(match, tuple):
                        match = match[0]
                    
                    ioc = match.strip()
                    if ioc and ioc.lower() not in seen:
                        iocs.append({
                            "ioc": ioc,
                            "type": ioc_type
                        })
                        seen.add(ioc.lower())
        
        return self._validate_and_normalize_iocs(iocs)
    
    def _parse_json_response(self, content: str) -> List[Dict[str, str]]:
        """Parse JSON response with multiple fallback strategies"""
        # Strategy 1: Direct JSON parse
        try:
            data = json.loads(content)
            if isinstance(data, list):
                return data
        except json.JSONDecodeError:
            pass
        
        # Strategy 2: Extract JSON array from text
        json_pattern = r'\[\s*\{.*?\}\s*\]'
        match = re.search(json_pattern, content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
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
        
        return iocs
    
    def _is_valid_ioc(self, item: Dict) -> bool:
        """Check if an IOC object is valid"""
        return (
            isinstance(item, dict) and
            "ioc" in item and
            "type" in item and
            isinstance(item["ioc"], str) and
            isinstance(item["type"], str) and
            item["ioc"].strip() and
            item["type"].strip()
        )
    
    def _validate_and_normalize_iocs(self, iocs: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Validate and normalize IOCs"""
        validated = []
        seen = set()
        
        for ioc_data in iocs:
            if not self._is_valid_ioc(ioc_data):
                continue
            
            # Normalize IOC
            normalized_ioc = self._normalize_ioc(ioc_data["ioc"])
            ioc_type = ioc_data["type"].lower()
            
            # Check for duplicates
            ioc_key = f"{normalized_ioc.lower()}|{ioc_type}"
            if ioc_key in seen:
                continue
            
            # Additional validation using regex if available
            if ioc_type in self.REGEX_PATTERNS:
                pattern = self.REGEX_PATTERNS[ioc_type]
                if not re.match(pattern, normalized_ioc, re.IGNORECASE):
                    print(f"[Chunker: ioc extractor] IOC failed validation: {normalized_ioc} (type: {ioc_type})")
                    continue
            
            validated.append({
                "ioc": normalized_ioc,
                "type": ioc_type
            })
            seen.add(ioc_key)
        
        return validated
    
    def _normalize_ioc(self, ioc: str) -> str:
        """Normalize obfuscated IOCs"""
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
