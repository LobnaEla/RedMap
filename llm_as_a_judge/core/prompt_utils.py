from typing import List


def create_judge_prompt(
    original_text: str,
    iocs: str,
    llm_predicted_techniques: List[str],  # Primary list to validate
    ras_evidence_techniques: List[
        str
    ],  # RAS reference for evidence and potential additions
) -> str:
    """
    Creates an enhanced forensic-style judge prompt that performs retroactive validation
    on techniques from both the LLM's predictions and the RAS results, using the original
    CTI text as the primary ground truth for evidence.

    This improved version addresses the need for comprehensive validation:
    - Considers the union of unique techniques from LLM predictions and RAS results.
    - For each unique technique (regardless of source), validates against the CTI text:
      check for real evidence, provide retroactive reasoning (why identified or why rejected).
    - Only validates a technique if there's strong alignment with the CTI text,
      using RAS as supplementary context (e.g., definitions, examples) but not as the decider.
    - Allows adding techniques from RAS to the validated list only if they are clearly
      supported by evidence in the CTI text, with detailed justification.
    - For LLM predictions, focuses on verifying if evidence truly exists or if it's a hallucination.
    - Emphasizes detailed, step-by-step reasoning for each decision to ensure transparency
      and scalability in analysis.
    - Dynamically handles inputs to make the prompt adaptable to varying list sizes,
      ensuring no static configurations.

    The goal is to improve F1 score by enhancing recall (via potential RAS additions)
    while maintaining high precision (strict text-based validation), avoiding mere
    intersections and favoring evidence-grounded decisions.

    Args:
        original_text: The original CTI text to serve as primary evidence.
        iocs: String representation of Indicators of Compromise.
        llm_predicted_techniques: List of techniques predicted by the LLM to audit.
        ras_evidence_techniques: List of techniques from RAS as evidence support and candidates for addition.

    Returns:
        A dynamically formatted prompt string for the LLM-as-judge.
    """

    # Dynamically compute unique techniques from union of LLM and RAS for comprehensive analysis
    all_techniques = sorted(
        set(llm_predicted_techniques) | set(ras_evidence_techniques)
    )
    num_all_techniques = len(all_techniques)
    llm_techniques_str = str(llm_predicted_techniques)  # Stringify for prompt insertion
    ras_techniques_str = str(ras_evidence_techniques)
    all_techniques_str = str(all_techniques)  # For reference in prompt

    # Build the prompt dynamically, interpolating variables for scalability
    prompt = f"""You are a senior MITRE ATT&CK forensic analyst and validation judge.
Your task is to perform **retroactive validation** on MITRE ATT&CK techniques identified from a Cyber Threat Intelligence (CTI) report. 
You will evaluate techniques sourced from two inputs: a Large Language Model (LLM) prediction via in-context learning, 
and Retrieval-Augmented Search (RAS) results from a MITRE knowledge base. 
The **original CTI text is the primary ground truth** for all validations—every decision must be anchored in evidence from the text.

## Mission: Retroactive Validation of Techniques from LLM and RAS
Consider the **union of unique techniques** from both LLM predictions and RAS results. 
For each unique technique, conduct a forensic audit:
1. **Evidence Check**: Is there explicit, implied, or strongly inferential evidence in the CTI text supporting this technique? Cite specific quotes or behaviors.
2. **Retroactive Reasoning**: 
   - **Why was it identified?** (If validated) Explain the alignment with text, attack phase, prerequisites, and operational fit. Reference RAS for supplementary context (e.g., technique definitions) if helpful.
   - **Why was it rejected?** (If rejected) Detail missing evidence, contradictions, or overgeneralizations. Explain potential hallucinations (for LLM-sourced) or mismatches (for RAS-sourced).
3. **Source Consideration**: Note if the technique came from LLM, RAS, or both. For RAS-only techniques, only validate and add if strongly aligned with text evidence—do not add based solely on RAS similarity.
4. **Decision**: Validate only if text evidence is clear and sufficient; be conservative to avoid false positives.

> **Critical Rule**: All validations are retroactive against the CTI text. RAS provides context (e.g., why a technique might fit) but cannot override lack of text evidence. 
> This ensures balanced recall (considering RAS for completeness) and precision (text-grounded decisions). Do not merely intersect lists—evaluate each independently.

---

## Original CTI Content
{original_text}


## Indicators of Compromise (IOCs)
{iocs}


---

## Inputs for Validation

### LLM-Predicted Techniques (From In-Context Learning)
{llm_techniques_str}

### RAS Evidence Techniques (From Semantic Search)
These provide supplementary context and potential additions:
{ras_techniques_str}

### Unique Techniques to Audit (Union for Comprehensive Review)
{all_techniques_str}

> Use RAS as a reference for technique details and synergies, but prioritize CTI text for evidence.

---

## Validation Framework

For each unique technique in the union list, perform the following:

### 1. Evidence Assessment
- Primary: Scan the CTI text for direct evidence (e.g., behaviors, tools, IOCs matching the technique).
- Secondary: Check if in RAS (for context support) or LLM (for original prediction).
- If RAS-only: Evaluate if text aligns with RAS-retrieved knowledge; add only with strong text justification.

### 2. Contextual Fit
- Alignment with attack phase, prerequisites, and overall narrative in the text.
- Operational plausibility based on described behaviors.

### 3. Confidence Scoring
- **High (0.8–1.0)**: Strong text evidence + presence in both LLM/RAS.
- **Medium (0.5–0.79)**: Strong text evidence but from one source, or weaker evidence with dual support.
- **Low (0.0–0.49)**: Insufficient text evidence, even if in sources.

> **Rule**: Reject if confidence < 0.5 (i.e., weak/no text evidence). For additions from RAS, require at least medium confidence.

### 4. Retroactive Reasoning
- Always explain: Why identified (evidence match) or rejected (evidence gap).
- For rejections: Suggest alternatives if a better-fitting technique exists in sources.

---

## Output Format (JSON)
{{
    "validated_techniques": [
        // All unique techniques (from LLM or RAS) that pass text-based validation, sorted
    ],
    "rejected_techniques": [
        // All unique techniques that fail validation, sorted
    ],
    "technique_analysis": {{
        "T1234": {{
            "status": "validated|rejected",
            "confidence": 0.92,
            "evidence": "Specific quote or behavior from text supporting/rejecting",
            "reasoning": "Detailed retroactive explanation: why identified (alignment details) or rejected (gaps, hallucinations); reference sources and RAS context if relevant",
            "from_llm": true|false,
            "from_ras": true|false,
            "alternative": "T5678 (if rejected, suggest better fit from sources)"
        }}
    }},
    "validation_summary": {{
        "total_analyzed": {num_all_techniques},
        "validated_count": 0,
        "rejected_count": 0,
        "validation_rate": 0.0,
        "from_llm_validated": 0,
        "from_ras_added": 0,  // Count of validated techniques that were RAS-only
        "hallucinated_count": 0  // LLM predictions rejected due to no evidence
    }}
}}


---

## Critical Directives

1. **Text as Ground Truth**: Every decision must cite CTI text evidence; RAS is for context, not proof.
2. **Retroactive Focus**: Provide explicit 'why identified' or 'why rejected' in reasoning for each.
3. **Additions from RAS**: Only if text strongly supports—justify inferences dynamically based on content.
4. **Prefer Sub-Techniques**: When text evidence allows specificity.
5. **Cite Exactly**: Use quotes from text for transparency and detailed explanations.
6. **Detect Issues Conservatively**: Flag hallucinations only for LLM predictions lacking text basis.
7. **Balanced & Scalable**: Analyze all unique techniques dynamically; explain in detail for reproducibility.

---

## Final Output Requirement
Reflect a thorough **retroactive forensic audit**, validating against text while leveraging sources for completeness. 
Output only techniques grounded in CTI evidence.

Begin your forensic validation now."""

    return prompt
