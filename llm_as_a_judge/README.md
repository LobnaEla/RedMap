Ce module implémente un système de validation croisée des techniques MITRE ATT&CK en utilisant un LLM comme juge pour analyser et valider les résultats combinés du RAG (Retrieval Augmented Search) et du premier LLM (In-Context Learning).

## Concept Clé

**Objectif** : Au lieu d'utiliser directement les résultats issus du RAG ou du LLM, le module :
1. **Analyse les deux sorties** (RAG + LLM) par rapport au chunk CTI original
2. **Effectue une vérification rétroactive** : "Pourquoi cette technique a-t-elle été proposée/rejetée ?"
3. **Produit une liste finale** des techniques validées après croisement des approches

## Architecture

```
/llm-as-a-judge/
├── core/
│   ├── validation_client.py    # Client LLM pour validation croisée
│   ├── technique_validator.py  # Validateur principal
│   ├── prompt_utils.py        # Prompts de validation
│   └── config.py              # Configuration
├── utils/
│   ├── validation_utils.py    # Analyses et métriques
│   └── file_utils.py          # Gestion des fichiers
├── tests/                     # Exemples d'utilisation
└── main.py                   # Script principal
```

## Processus de Validation

### 1. Analyse des Entrées
```python
# Techniques communes (intersection)
common_techniques = RAG ∩ LLM

# Techniques uniques à chaque approche  
rag_only = RAG - LLM
llm_only = LLM - RAG
```

### 2. Validation Rétroactive
Pour chaque technique, le LLM juge analyse :
- **Evidence** : Quelle preuve textuelle supporte cette technique ?
- **Contextuel** : Cette technique correspond-elle au scénario décrit ?
- **Pourquoi proposée** : Quelle logique a mené à cette suggestion ?
- **Pourquoi rejetée** : Pourquoi l'autre approche l'a-t-elle manquée ?

### 3. Sortie Finale
```json
{
    "validated_techniques": ["T1059.001", "T1053.005"],
    "rejected_techniques": ["T1002", "T1090"],
    "technique_analysis": {
        "T1059.001": {
            "status": "validated",
            "confidence": 0.95,
            "evidence": "PowerShell usage mentioned in original text",
            "source": "common"
        }
    }
}
```

## Fonctionnalités

### ✅ Validation Croisée
- Analyse des techniques communes (haute confiance)
- Évaluation des techniques RAG-only
- Évaluation des techniques LLM-only
- Identification des techniques manquées

### 📊 Métriques Détaillées
- Taux de validation par source (commune/RAG-only/LLM-only)
- Scores de confiance par technique
- Analyse de la fiabilité du consensus
- Contribution de chaque approche

### 🔍 Analyse Rétroactive
- Explication des décisions de validation
- Identification des forces/faiblesses de chaque approche
- Recommandations opérationnelles

## Utilisation

### Installation
```bash
pip install google-generativeai numpy
export GEMINI_API_KEY="your_api_key"
```

### Utilisation Basique
```python
from llm_as_a_judge import TechniqueValidator

validator = TechniqueValidator(api_key="your_api_key")

# Validation d'un chunk
result = validator.validate_single_chunk(
    chunk_data={
        "chunk_id": "001",
        "text": "CTI content...",
        "iocs": "indicators..."
    },
    rag_results=["T1059.001", "T1105"],  # Techniques RAG
    llm_results=["T1059.001", "T1053.005"]  # Techniques LLM
)

# Techniques finales validées
final_techniques = result["final_validated_techniques"]
```

### Validation en Batch
```python
results = validator.batch_validate(
    chunks=chunk_list,
    rag_results_list=rag_results,
    llm_results_list=llm_results
)

# Extraction des techniques finales pour tous les chunks
final_techniques = validator.extract_final_techniques(results)
```

## Format des Données

### Entrée
```python
# Chunk CTI
{
    "chunk_id": "unique_id",
    "text": "Original CTI content",
    "iocs": "indicators of compromise"
}

# Résultats RAG et LLM
rag_results = ["T1059.001", "T1105", "T1053.005"]
llm_results = ["T1059.001", "T1547.001", "T1053.005"]
```

### Sortie
```python
{
    "chunk_id": "001",
    "success": True,
    "input_analysis": {
        "rag_techniques": ["T1059.001", "T1105", "T1053.005"],
        "llm_techniques": ["T1059.001", "T1547.001", "T1053.005"],
        "common_techniques": ["T1059.001", "T1053.005"],
        "rag_only_techniques": ["T1105"],
        "llm_only_techniques": ["T1547.001"]
    },
    "final_validated_techniques": ["T1059.001", "T1053.005", "T1105"],
    "validation_result": {
        "technique_analysis": {
            "T1059.001": {
                "status": "validated",
                "confidence": 0.95,
                "evidence": "PowerShell mentioned in text",
                "source": "common"
            }
        }
    }
}
```

## Métriques et Insights

### Métriques de Validation
- **Taux de validation global** : % de techniques validées sur l'ensemble
- **Précision du consensus** : % de techniques communes validées
- **Contribution RAG** : Valeur ajoutée des techniques RAG-only
- **Contribution LLM** : Valeur ajoutée des techniques LLM-only

### Insights Opérationnels
- **Fiabilité du consensus** : High/Medium/Low
- **Forces de chaque approche**
- **Techniques manquées** par les deux approches
- **Recommandations** pour les équipes SOC

## Intégration Pipeline

```
Chunks CTI → RAG System → Techniques RAG
     ↓            ↓
     → LLM ICL → Techniques LLM
                    ↓
              LLM-as-a-Judge
                    ↓
            Techniques Validées
```

## Tests et Validation

```bash
# Exemple d'utilisation
python -m llm_as_a_judge.tests.usage_example.py

# Exécution complète
python -m llm_as_a_judge.main.py
```