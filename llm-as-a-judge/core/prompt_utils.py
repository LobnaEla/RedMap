def create_judge_prompt(
    original_text: str, rag_techniques: List[str], icl_techniques: List[str]
) -> str:
    """
    Crée un prompt pour l'évaluation comparative des techniques MITRE

    Args:
        original_text: Texte CTI original
        rag_techniques: Techniques proposées par RAG
        icl_techniques: Techniques proposées par ICL

    Returns:
        Prompt formaté pour l'évaluation
    """

    prompt = f"""You are an expert cybersecurity analyst specialized in MITRE ATT&CK framework evaluation. Your task is to compare and evaluate two different approaches for mapping Cyber Threat Intelligence (CTI) to MITRE ATT&CK techniques.

## Task Overview
You will evaluate two sets of MITRE technique mappings for the same CTI content:
1. **RAG (Retrieval Augmented Generation)**: Uses semantic similarity to retrieve relevant techniques
2. **ICL (In-Context Learning)**: Uses direct LLM inference with few-shot examples

## Evaluation Criteria

### 1. Accuracy (30% weight)
- Are the proposed techniques correct for the described behaviors?
- Do the techniques align with their official MITRE definitions?
- Are there any hallucinated or incorrect technique IDs?

### 2. Coverage (25% weight)  
- How comprehensively do the techniques cover the described attack behaviors?
- Are important techniques missing?
- Is there appropriate granularity (parent vs sub-techniques)?

### 3. Relevance (25% weight)
- How well do the techniques match the specific context of the CTI?
- Are the techniques operationally relevant for this scenario?
- Do the techniques reflect the actual attacker TTPs described?

### 4. Specificity (20% weight)
- Are sub-techniques used when appropriate?
- Is the level of detail appropriate for the description?
- Are generic techniques avoided when specific ones apply?

## Original CTI Content
```
{original_text}
```

## RAG Approach Results
Proposed techniques: {rag_techniques}

## ICL Approach Results  
Proposed techniques: {icl_techniques}

## Evaluation Instructions

1. **Analyze Each Approach**: Evaluate both RAG and ICL results against the four criteria
2. **Score Each Criterion**: Rate each approach on a scale of 0.0 to 1.0 for each criterion
3. **Calculate Overall Scores**: Apply the weighted scoring system
4. **Determine Winner**: Choose the better approach or declare a tie
5. **Provide Reasoning**: Explain your evaluation decision

## Output Format
Provide your evaluation as a JSON object with the following structure:

```json
{{
    "winner": "rag|icl|tie",
    "rag_score": <overall_weighted_score_0_to_1>,
    "icl_score": <overall_weighted_score_0_to_1>,
    "accuracy_rag": <accuracy_score_0_to_1>,
    "accuracy_icl": <accuracy_score_0_to_1>,
    "coverage_rag": <coverage_score_0_to_1>,
    "coverage_icl": <coverage_score_0_to_1>,
    "relevance_rag": <relevance_score_0_to_1>,
    "relevance_icl": <relevance_score_0_to_1>,
    "specificity_rag": <specificity_score_0_to_1>,
    "specificity_icl": <specificity_score_0_to_1>,
    "reasoning": "Detailed explanation of evaluation decision, highlighting strengths and weaknesses of each approach",
    "rag_strengths": ["list", "of", "rag", "strengths"],
    "rag_weaknesses": ["list", "of", "rag", "weaknesses"],
    "icl_strengths": ["list", "of", "icl", "strengths"], 
    "icl_weaknesses": ["list", "of", "icl", "weaknesses"],
    "missing_techniques": ["techniques", "that", "both", "approaches", "missed"],
    "incorrect_techniques": ["techniques", "that", "are", "incorrect", "or", "hallucinated"]
}}
```

## Critical Guidelines
- Be objective and evidence-based in your evaluation
- Consider both false positives (incorrect techniques) and false negatives (missing techniques)
- Evaluate based on the specific CTI content provided, not general knowledge
- Prefer specific sub-techniques over generic parent techniques when warranted
- Consider operational utility for security teams
- Provide constructive feedback for improvement

Begin your evaluation now."""

    return prompt
