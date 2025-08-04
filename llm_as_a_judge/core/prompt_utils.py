from typing import List


def create_judge_prompt(
    original_text: str,
    iocs: str,
    common_techniques: List[str],
    rag_only_techniques: List[str],
    llm_only_techniques: List[str],
    all_techniques: List[str],
) -> str:
    """
    Crée un prompt pour la validation croisée des techniques MITRE

    Args:
        original_text: Texte CTI original
        iocs: Indicateurs de compromission
        common_techniques: Techniques communes aux deux approches
        rag_only_techniques: Techniques uniquement proposées par RAG
        llm_only_techniques: Techniques uniquement proposées par LLM
        all_techniques: Toutes les techniques à analyser

    Returns:
        Prompt formaté pour la validation
    """

    prompt = f"""You are an expert cybersecurity analyst specialized in MITRE ATT&CK framework validation. Your task is to perform cross-validation of MITRE technique mappings by analyzing techniques proposed by two different approaches (RAG/Retrieval Augmented Search and Direct LLM Inference) against the original CTI content.

## Mission Overview
You will validate techniques through retroactive verification - for each technique, you must determine:
1. **WHY was this technique proposed?** (What evidence supports it?)
2. **WHY was this technique rejected by the other approach?** (What evidence is missing?)
3. **Should this technique be included in the final validated list?**

## Original CTI Content
```
{original_text}
```

## Indicators of Compromise (IOCs)
```
{iocs}
```

## Technique Analysis Breakdown

### Common Techniques (Agreed by both RAG and LLM)
**High confidence candidates**: {common_techniques}
- These techniques were identified by BOTH approaches
- Likely to be valid, but still require verification against the original content

### RAG-Only Techniques (Missed by LLM)
**RAG proposed, LLM missed**: {rag_only_techniques}
- Why did RAG suggest these? (Semantic similarity to technique descriptions)
- Why did LLM miss these? (Not in training examples, context issues?)
- Are these false positives or missed opportunities?

### LLM-Only Techniques (Missed by RAG)  
**LLM proposed, RAG missed**: {llm_only_techniques}
- Why did LLM suggest these? (Pattern recognition, contextual inference)
- Why did RAG miss these? (Not in vector database, poor semantic match?)
- Are these valid insights or hallucinations?

## Validation Framework

### For Each Technique, Perform Retroactive Analysis:

1. **Evidence Assessment**
   - What specific text/behavior in the CTI supports this technique?
   - Do the IOCs align with this technique's typical indicators?
   - Is the technique definition compatible with described activities?

2. **Contextual Validation**
   - Does this technique fit the attack phase/context described?
   - Are prerequisites for this technique present in the scenario?
   - Does this technique make operational sense given other validated techniques?

3. **Confidence Scoring**
   - High (0.8-1.0): Strong textual evidence, clear behavioral match
   - Medium (0.5-0.79): Some evidence, reasonable inference required
   - Low (0.0-0.49): Weak evidence, speculative or incorrect

4. **Rejection Analysis**
   - If rejecting: What specific evidence is missing?
   - If rejecting: What alternative technique better fits the evidence?
   - Document why the other approach might have suggested this technique

## Output Format
Provide your validation as a JSON object:

```json
{{
    "validated_techniques": [
        "list of techniques that pass validation with evidence"
    ],
    "rejected_techniques": [
        "list of techniques that fail validation"
    ],
    "technique_analysis": {{
        "T1234": {{
            "status": "validated|rejected", 
            "confidence": 0.85,
            "evidence": "Specific text from CTI that supports this technique",
            "reasoning": "Why this technique is valid/invalid for this scenario",
            "source": "common|rag_only|llm_only",
            "alternative": "T5678 (if rejected, suggest better alternative)"
        }}
    }},
    "validation_summary": {{
        "total_analyzed": {len(all_techniques)},
        "validated_count": 0,
        "rejected_count": 0,
        "validation_rate": 0.0,
        "high_confidence_count": 0,
        "medium_confidence_count": 0,
        "low_confidence_count": 0
    }},
    "cross_validation_insights": {{
        "rag_strengths": ["What RAG did well"],
        "rag_weaknesses": ["What RAG missed or got wrong"],
        "llm_strengths": ["What LLM did well"], 
        "llm_weaknesses": ["What LLM missed or got wrong"],
        "consensus_accuracy": "How accurate were the common techniques",
        "complementary_value": "How the approaches complement each other"
    }},
    "missing_techniques": [
        "techniques that both approaches missed but should be present"
    ],
    "operational_recommendations": [
        "actionable recommendations for SOC teams based on validated techniques"
    ]
}}
```

## Critical Validation Guidelines

1. **Evidence-Based**: Every validation decision must cite specific textual evidence
2. **Retroactive Reasoning**: Explain why each approach proposed/missed each technique
3. **Conservative Validation**: When in doubt, require stronger evidence
4. **Operational Focus**: Prioritize techniques useful for detection and response
5. **Avoid Confirmation Bias**: Don't automatically validate common techniques
6. **Consider False Negatives**: Identify techniques both approaches missed
7. **Specificity Preference**: Prefer specific sub-techniques over generic parents when evidence supports them

## Analysis Priority
1. Start with common techniques (highest confidence candidates)
2. Analyze RAG-only techniques (potential semantic matches)
3. Analyze LLM-only techniques (potential pattern recognition)
4. Identify any missing techniques both approaches overlooked
5. Provide final validated technique list with confidence scores

Begin your cross-validation analysis now, focusing on retroactive verification and evidence-based validation."""

    return prompt
