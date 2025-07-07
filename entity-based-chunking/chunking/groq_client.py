import json
import requests
from typing import List, Dict, Optional
import yaml
import os

class GroqClient:
    """Client for interacting with the Groq API for IOC extraction."""
    def __init__(self, api_key: Optional[str] = None, config: dict = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("Groq API key not provided")
        if config is None:
            raise ValueError("Config dictionary must be provided")
        self.base_url = config["groq"]["api_url"]
        self.model = config["groq"]["model"]
        self.temperature = config["groq"].get("temperature", 0.1)
        self.system_prompt = (
            config["prompts"]["ioc_extraction"]
            + "\n\nIMPORTANT: Respond ONLY with a JSON array of objects, no explanation, no markdown, no notes, no code block, no commentary."
        )
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def extract_iocs(self, text: str) -> List[Dict[str, str]]:
        """Extract IOCs from text using Groq's LLM. Handles non-JSON responses robustly."""
        try:
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
                }
            )
            response.raise_for_status()
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            print("[Groq LLM raw content]:\n", content) # Debugging output
            # Try direct JSON parse first
            try:
                return json.loads(content)
            except Exception:
                # Try to extract the first JSON array from the text
                import re
                match = re.search(r'(\[.*?\])', content, re.DOTALL)
                if match:
                    json_str = match.group(1)
                    try:
                        return json.loads(json_str)
                    except Exception as e2:
                        print(f"[GroqClient] Failed to parse extracted JSON: {e2}")
                print("[GroqClient] Could not extract valid JSON from LLM response.")
                return []
        except Exception as e:
            print(f"Error extracting IOCs: {str(e)}")
            return []
