import json
import time
from datetime import datetime
from typing import List, Dict, Optional

import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, GoogleAPIError

from .prompt_utils import create_judge_prompt


class JudgeClient:
    """Client LLM for validating LLM predictions using RAS evidence."""

    def __init__(self, api_key: str, model_config: Optional[Dict] = None):
        genai.configure(api_key=api_key)
        self.config = model_config or {
            "model": "gemini-1.5-flash",
            "temperature": 0.1,
            "max_retries": 3,
        }
        self.model = genai.GenerativeModel(self.config["model"])

    def validate_llm_predictions(
        self,
        original_chunk: str,
        llm_predicted_techniques: List[str],
        ras_evidence_techniques: List[str],
        chunk_id: str,
        iocs: str = "",
    ) -> Dict:
        """Validate LLM predicted techniques using RAS evidence."""

        if not original_chunk.strip():
            return self._create_error_result(chunk_id, "Empty original chunk")

        # Clean inputs
        llm_clean = self._clean_techniques(llm_predicted_techniques)
        ras_clean = self._clean_techniques(ras_evidence_techniques)

        # Create validation prompt
        prompt = create_judge_prompt(
            original_text=original_chunk,
            iocs=iocs,
            llm_predicted_techniques=llm_clean,
            ras_evidence_techniques=ras_clean,
        )

        for attempt in range(1, self.config["max_retries"] + 1):
            try:
                response = self.model.generate_content(
                    prompt,
                    generation_config={
                        "temperature": self.config["temperature"],
                        "response_mime_type": "application/json",
                    },
                )

                content = (
                    response.text.strip()
                    if response and hasattr(response, "text")
                    else ""
                )

                if content:
                    judge_result = self._parse_judge_response(content)
                    return self._create_success_result(
                        chunk_id=chunk_id,
                        original_chunk=original_chunk,
                        iocs=iocs,
                        llm_predicted=llm_clean,
                        ras_evidence=ras_clean,
                        validation=judge_result,
                    )

            except ResourceExhausted:
                wait_time = 60**attempt
                print(f"Rate limit exceeded. Retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue

            except (GoogleAPIError, Exception) as e:
                error_msg = f"API error: {str(e)}"
                print(error_msg)
                if attempt == self.config["max_retries"]:
                    return self._create_error_result(chunk_id, error_msg)
                continue

        return self._create_error_result(
            chunk_id, f"Failed after {self.config['max_retries']} attempts"
        )

    def _clean_techniques(self, techniques: List[str]) -> List[str]:
        """Clean and validate MITRE techniques."""
        if not isinstance(techniques, list):
            return []
        cleaned = []
        for tech in techniques:
            if isinstance(tech, str):
                tech = tech.strip().upper()
                if tech.startswith("T") and any(c.isdigit() for c in tech):
                    cleaned.append(tech)
            elif isinstance(tech, dict):
                # Handle RAG technique objects with technique_id field
                tech_id = tech.get("technique_id", "")
                if isinstance(tech_id, str):
                    # Extract technique ID from MitreDocument format
                    # e.g., "MitreDocument(id=T1583.006, name=Web Services)" -> "T1583.006"
                    import re
<<<<<<< HEAD

                    match = re.search(r"id=([T]\d+(?:\.\d+)?)", tech_id)
=======
                    match = re.search(r'id=([T]\d+(?:\.\d+)?)', tech_id)
>>>>>>> b9a37a5d7b072bd2acb3feec7724d58483212e0d
                    if match:
                        cleaned.append(match.group(1))
        return cleaned

    def _parse_judge_response(self, response: str) -> Dict:
        """Parse judge response and extract validated techniques."""
        try:
            # Clean response
            cleaned = response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:].split("```", 1)[0].strip()
            elif cleaned.startswith("```"):
                cleaned = cleaned[3:].split("```", 1)[0].strip()

            # Parse JSON
            result = json.loads(cleaned)

            # Extract and validate structure
            validated = result.get("validated_techniques", [])
            rejected = result.get("rejected_techniques", [])
            analysis = result.get("technique_analysis", {})

            # Clean technique IDs
            def clean_tech(tech):
                if isinstance(tech, str):
                    tech = tech.strip().upper()
                    if tech.startswith("T") and any(c.isdigit() for c in tech):
                        return tech
                return None

            validated_clean = [t for t in (clean_tech(t) for t in validated) if t]
            rejected_clean = [t for t in (clean_tech(t) for t in rejected) if t]

            return {
                "validated_techniques": validated_clean,
                "rejected_techniques": rejected_clean,
                "technique_analysis": analysis,
                "success": True,
                "raw_response": response,
            }

        except json.JSONDecodeError as e:
            print(f"❌ JSON parse error: {e}")
            return self._create_parse_error_result(response, str(e))

        except Exception as e:
            print(f"❌ Unexpected parsing error: {e}")
            return self._create_parse_error_result(response, str(e))

    def _create_parse_error_result(self, response: str, error: str) -> Dict:
        """Create parse error result."""
        return {
            "validated_techniques": [],
            "rejected_techniques": [],
            "technique_analysis": {},
            "success": False,
            "raw_response": response[:500],
            "parse_error": True,
        }

    def _create_success_result(
        self,
        chunk_id: str,
        original_chunk: str,
        iocs: str,
        llm_predicted: List[str],
        ras_evidence: List[str],
        validation: Dict,
    ) -> Dict:
        """Create successful validation result."""

        return {
            "chunk_id": chunk_id,
            "original_chunk": original_chunk,
            "iocs": iocs,
            "llm_techniques": llm_predicted,
            "ras_techniques": ras_evidence,
            "judge_result": validation,
            "final_validated_techniques": validation.get("validated_techniques", []),
            "success": True,
            "timestamp": datetime.now().isoformat(),
        }

    def _create_error_result(self, chunk_id: str, error: str) -> Dict:
        """Create error result."""
        return {
            "chunk_id": chunk_id,
            "error": error,
            "success": False,
            "timestamp": datetime.now().isoformat(),
        }
