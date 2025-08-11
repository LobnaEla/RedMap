from typing import List


def create_judge_prompt(
    original_text: str,
    iocs: str,
    llm_predicted_techniques: List[str],
    ras_evidence_techniques: List[str],
) -> str:
    """
    Creates a forensic judge prompt for validating MITRE ATT&CK techniques against CTI evidence.
    Validates techniques from LLM predictions and RAS results, requiring explicit text evidence.
    Rejects techniques with insufficient or contradictory evidence.

    Args:
        original_text: Raw CTI text (primary evidence source).
        iocs: Extracted IOCs (for technique cross-validation).
        llm_predicted_techniques: Techniques proposed by LLM (may contain hallucinations).
        ras_evidence_techniques: Techniques from RAS (contextual support, not standalone evidence).

    Returns:
        A structured prompt for the LLM-as-judge with forensic validation rules.
    """

    prompt = f"""You are a senior MITRE ATT&CK forensic analyst. Your task is to validate whether 
techniques proposed by an LLM or RAS are **explicitly supported** by evidence in the CTI text.

# Rules for Validation
1. **Ground Truth**: The original CTI text is the **only** source of truth. Techniques must be:
   - Directly described (e.g., "the attacker used PsExec for lateral movement" → T1021.002), OR
   - Strongly inferred (e.g., "deployed a keylogger" → T1056.001 with no alternative explanation).
2. **RAS Context**: RAS-provided techniques are **not evidence**—they must also align with the text.
3. **Rejection Criteria**: Reject a technique if:
   - No text evidence exists (even if in RAS/LLM),
   - Evidence is ambiguous (e.g., "accessed files" ≠ T1005),
   - A sub-technique better fits the evidence.

# Validation Steps
For each technique in the **combined list** (LLM + RAS):
1. **Evidence Check**: 
   - Scan the text for explicit matches to the technique's procedure, tool, or outcome.
   - Cite exact quotes or describe unambiguous behaviors.
2. **Confidence Scoring**:
   - **High (0.8-1.0)**: Direct quote or exact behavioral match.
   - **Medium (0.5-0.79)**: Logical inference with no contradictions.
   - **Low (<0.5)**: Reject (insufficient evidence).
3. **Source Analysis**:
   - Flag LLM-proposed techniques with no evidence as *potential hallucinations*.
   - For RAS techniques, verify text alignment *without* relying on RAS content.

# Input Data
## CTI Text (Primary Evidence)
{original_text}

## IOCs (Corroborative Context)
{iocs}

## Techniques to Validate
- LLM-Proposed: {llm_predicted_techniques}
- RAS-Suggested: {ras_evidence_techniques}

# Output Format (JSON)
{{
  "validated_techniques": [
    {{
      "technique_id": "TXXXX",
      "confidence": 0.0-1.0,
      "evidence": ["exact quotes", "behavioral descriptions"],
      "source": "llm|ras|both"
    }}
  ],
  "rejected_techniques": [
    {{
      "technique_id": "TXXXX",
      "reason": "no_evidence|ambiguous|better_alternative",
      "missing_evidence": "Expected but not found in text",
      "source": "llm|ras"
    }}
  ],
  "statistics": {{
    "validated_total": int,
    "rejected_total": int,
    "llm_hallucinations": int  # LLM proposals with zero evidence
  }}
}}

# Critical Directives
- **Be conservative**: Only validate techniques with clear evidence.
- **Prioritize sub-techniques** when evidence allows (e.g., T1071.001 over T1071).
- **Explain rejections**: State what evidence was missing or conflicting.
- **Do not** invent evidence to fit RAS/LLM suggestions.

Begin validation now. For each technique, provide: 
1. Evidence (or lack thereof), 
2. Confidence score, 
3. Final decision (validate/reject)."""
