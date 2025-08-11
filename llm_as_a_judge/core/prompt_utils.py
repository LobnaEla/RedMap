from typing import List


def create_judge_prompt(
    original_text: str,
    iocs: str,
    llm_predicted_techniques: List[str],
    ras_evidence_techniques: List[str],
) -> str:
    """
    Explicitly performs retroactive validation of LLM-proposed techniques against CTI text evidence,
    with RAS providing context for rejected techniques and alternatives.
    Only returns techniques with clear CTI alignment.
    """

    prompt = f"""### Role  
You are a **forensic MITRE ATT&CK validator** performing **retroactive validation** of techniques.  

### Core Mission  
1. **For each LLM-proposed technique**:  
   - Audit **why it was identified** (what in the text triggered it?).  
   - Verify if it **truly aligns** with CTI text evidence (explicit or strongly implied).  
   - Reject if no evidence exists (even if in RAS).  

2. **For RAS top-{len(ras_evidence_techniques)} techniques**:  
   - Provide **contextual support** (e.g., "RAS suggests T1059 because text mentions 'command-line'").  
   - Explain **why rejected** if not validated (e.g., "Text lacks tool-specific evidence for T1059.001").  
   - Suggest **alternatives** (from RAS or elsewhere) if better fits exist.  

3. **Final Output**:  
   - **Only include techniques** with CTI evidence (no RAS-only additions without text support).  
   - **Flag hallucinations** (LLM proposals with zero evidence).  

---

### Input Data  
#### CTI Text (Ground Truth)  
{original_text}  

#### IOCs (Corroborative Context)  
{iocs}  

#### Techniques to Validate  
- **LLM-Predicted (Primary Audit Targets)**: {llm_predicted_techniques}  
- **RAS Contextual Suggestions (Top-{len(ras_evidence_techniques)})**: {ras_evidence_techniques}  

---

### Validation Process  
For **each unique technique** (LLM + RAS combined):  

1. **Retroactive LLM Audit**  
   - *Why identified?*: Trace the LLM's reasoning (e.g., "Text mentions 'credential dumping' → T1003").  
   - *Evidence check*:  
     - **Explicit**: Direct match (e.g., "used Mimikatz" → T1003).  
     - **Implied**: Logical fit (e.g., "accessed LSASS" → likely T1003).  
     - **Reject**: No evidence (e.g., "T1059 claimed but no CLI activity described").  

2. **RAS Context Analysis**  
   - *For rejected techniques*:  
     - Explain if RAS provided **near-miss context** (e.g., "RAS suggested T1059.001 but text only mentions 'commands', not scripting").  
     - Propose **better alternatives** (e.g., "Use T1059.003 instead for PowerShell evidence").  

3. **Confidence Thresholds**  
   - **High (≥0.8)**: Explicit text match.  
   - **Medium (≥0.5)**: Implied + RAS-supported.  
   - **Low (<0.5)**: Reject (no evidence).  

---

### Output Format (Original JSON)  
{{
    "validated_techniques": [
        // Only techniques with CTI evidence (explicit/implied)  
    ],
    "rejected_techniques": [
        // Techniques failing validation + RAS context for near-misses  
    ],
    "technique_analysis": {{
        "TXXXX": {{
            "status": "validated|rejected",
            "confidence": 0.0-1.0,
            "evidence": "Exact quotes or logical inference",
            "reasoning": "Retroactive explanation: Why LLM proposed it + evidence gap (if rejected)",
            "from_llm": true|false,
            "from_ras": true|false,
            "alternative": "Better technique (if rejected, from RAS or manual suggestion)"
        }}
    }},
    "validation_summary": {{
        "total_analyzed": int,
        "validated_count": int,
        "rejected_count": int,
        "validation_rate": float,
        "from_llm_validated": int,
        "from_ras_added": int,  // RAS-originated but text-validated
        "hallucinated_count": int  // LLM proposals with zero evidence
    }}
}}

### Critical Directives
1. **Retroactive First: Always explain** **why the LLM proposed each technique** before validating.
2. **RAS as Context, Not Evidence**: Use RAS to:
    - Explain rejections (e.g., "RAS suggested T1021.002, but text lacks RDP-specific evidence").
    - Suggest alternatives (e.g., "T1021.001 fits better for observed PsExec").
3. **No RAS-Only Additions**: Only include RAS techniques if **text evidence exists**.
4. **Confidence-Driven**: Reject all techniques with **low confidence (<0.5)**.

### Example Validation
**Technique**: T1059 (Command-Line Interface)
- **LLM Rationale**: "Text mentions 'executed malicious commands'."
- **Evidence Check**: Validated (Implied)
- **Quote**: "attacker ran 'net user /add' via cmd.exe"
- **Confidence**: 0.9 (High)

**Technique**: T1110.001 (Password Guessing)
- **LLM Rationale**: "Text says 'brute-forced credentials'."
- **RAS Context**: Suggests T1110.002 (Keylogging) as alternative.
- **Evidence Check**: Rejected
- **Missing Evidence**: No tool/behavior specifics (e.g., Hydra, Medusa).
- **Alternative**: T1003 (Credential Dumping) fits better per text."""
