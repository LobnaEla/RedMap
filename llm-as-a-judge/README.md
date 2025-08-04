# LLM-as-a-Judge Module

Ce module implémente un système d'évaluation comparative entre les approches RAG (Retrieval Augmented Generation) et ICL (In-Context Learning) pour le mapping de techniques MITRE ATT&CK.

## Architecture

```
/llm-as-a-judge/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── config.py          # Configuration du module
│   ├── judge_client.py    # Client LLM pour l'évaluation
│   ├── evaluator.py       # Évaluateur principal
│   └── prompt_utils.py    # Utilitaires de prompts
├── utils/
│   ├── __init__.py
│   ├── metrics.py         # Calculs de métriques
│   └── file_utils.py      # Utilitaires de fichiers
├── tests/
│   ├── test_judge_client.py
│   ├── test_evaluator.py
│   └── test_metrics.py
├── examples/
│   └── usage_example.py
├── main.py
└── README.md
```

## Fonctionnalités

### 1. Évaluation Comparative
- **Critères d'évaluation** :
  - Accuracy (30%) : Justesse des techniques proposées
  - Coverage (25%) : Couverture des comportements décrits
  - Relevance (25%) : Pertinence contextuelle
  - Specificity (20%) : Spécificité des techniques

### 2. Métriques Détaillées
- Scores individuels par critère
- Scores globaux pondérés
- Statistiques agrégées
- Identification du "gagnant" par chunk

### 3. Gestion des Données
- Support des formats JSON
- Sauvegarde des résultats détaillés
- Logging complet des évaluations

## Utilisation

### Installation des Dépendances
```bash
pip install google-generativeai numpy
```

### Configuration
```python
# Variables d'environnement requises
export GEMINI_API_KEY="your_gemini_api_key"
```

### Utilisation Basique
```python
from llm_as_a_judge import TechniqueEvaluator

# Initialisation
evaluator = TechniqueEvaluator(api_key="your_api_key")

# Évaluation d'un chunk unique
chunk_data = {
    "chunk_id": "001",
    "text": "Malware content...",
    "iocs": "indicators..."
}

result = evaluator.evaluate_single_chunk(
    chunk_data=chunk_data,
    rag_results=["T1059.001", "T1105"],
    icl_results=["T1059.001", "T1053.005"]
)
```

### Évaluation en Batch
```python
results = evaluator.batch_evaluate(
    chunks=chunk_list,
    rag_results_list=rag_results,
    icl_results_list=icl_results
)

# Sauvegarde des résultats
from llm_as_a_judge import save_evaluation_results
output_file = save_evaluation_results(results)
```

## Format des Données

### Input Chunk
```json
{
    "chunk_id": "unique_identifier",
    "text": "CTI content to analyze",
    "iocs": "indicators of compromise",
    "source_file": "original_file.pdf"
}
```

### Résultats RAG/ICL
```python
# Liste de techniques MITRE
["T1059.001", "T1105", "T1053.005"]
```

### Output d'Évaluation
```json
{
    "chunk_id": "001",
    "success": true,
    "evaluation": {
        "winner": "rag|icl|tie",
        "rag_score": 0.75,
        "icl_score": 0.68,
        "accuracy_rag": 0.8,
        "accuracy_icl": 0.7,
        "coverage_rag": 0.7,
        "coverage_icl": 0.6,
        "relevance_rag": 0.8,
        "relevance_icl": 0.7,
        "specificity_rag": 0.7,
        "specificity_icl": 0.6,
        "reasoning": "Detailed explanation...",
        "rag_strengths": ["strength1", "strength2"],
        "rag_weaknesses": ["weakness1"],
        "icl_strengths": ["strength1"],
        "icl_weaknesses": ["weakness1", "weakness2"]
    }
}
```

## Tests

```bash
# Exécuter tous les tests
python -m pytest llm-as-a-judge/tests/

# Test spécifique
python -m pytest llm-as-a-judge/tests/test_judge_client.py
```

## Intégration avec le Pipeline Existant

Le module s'intègre facilement avec votre pipeline CTI existant :

1. **Données d'entrée** : Utilise les chunks du pipeline CTI
2. **Résultats RAG** : À intégrer avec votre système RAG
3. **Résultats ICL** : Utilise les résultats du module LLM existant
4. **Sortie** : Produit des évaluations comparatives détaillées

## Exemple d'Exécution

```bash
cd /llm-as-a-judge/
export GEMINI_API_KEY="your_key"
python main.py
```

## Personnalisation

### Modification des Critères d'Évaluation
```python
# Dans core/config.py
JUDGE_CONFIG = {
    "evaluation_criteria": {
        "accuracy": 0.4,     # Augmenter le poids de l'accuracy
        "coverage": 0.3,     # Modifier les pondérations
        "relevance": 0.2,
        "specificity": 0.1
    }
}
```

### Prompts Personnalisés
Modifiez `core/prompt_utils.py` pour adapter les prompts d'évaluation à vos besoins spécifiques.

## Notes Importantes

1. **Rate Limiting** : Le module gère automatiquement les limites de taux de l'API Gemini
2. **Validation** : Validation automatique des formats de techniques MITRE
3. **Logging** : Logging détaillé pour le debugging et le monitoring
4. **Extensibilité** : Architecture modulaire pour faciliter les extensions