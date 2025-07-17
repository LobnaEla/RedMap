def create_mitre_prompt(text: str, iocs: list[str] = None) -> str:
    """
    Crée un prompt structuré pour le mapping MITRE ATT&CK

    Args:
        text: Texte CTI à analyser
        iocs: Liste des indicateurs de compromission

    Returns:
        Prompt formaté pour l'API Claude
    """
    base_prompt = """You are a cybersecurity expert specialized in the MITRE ATT&CK framework. Your task is to analyze a Cyber Threat Intelligence (CTI) description and identify the most relevant MITRE ATT&CK technique(s) based on the described behaviors.

Task Instructions:
Input Analysis: Analyze the provided CTI threat description to extract Indicators of Compromise (IoCs), attacker behaviors, and attack stages.
MITRE ATT&CK Mapping: Map these behaviors to the corresponding MITRE ATT&CK techniques (format: T#### or T####.### for sub-techniques).
Few-Shot Examples: Use the examples below as guidance for accurate mapping.
Multiple Techniques Handling: If multiple techniques apply, return all that are relevant. Prioritize specific sub-techniques over general ones when applicable.
Ambiguity Management: If unsure, choose the most likely technique based on semantic similarity to known MITRE descriptions. Avoid generic or overly broad techniques.
Validation: Ensure each identified technique aligns logically with the attack phase described and is compatible with SIEM/SOAR systems.
Output Format: Return only a JSON list of MITRE ATT&CK codes without additional explanations.

Few-Shot Examples:
Example 1
Description: "The adversary uses PowerShell to execute malicious payloads."
Identified Techniques: ["T1059", "T1484.001"]

Example 2
Description: "Malware collects system information using built-in OS tools."
Identified Techniques: ["T1082"]

Example 3
Description: "Data is exfiltrated through DNS requests to an external domain."
Identified Techniques: ["T1048", "T1048.003"]

Threat Description:
"{text}"

Response Format:
["T####", "T####.###", ...]"""

    # Ajout des IOCs si disponibles
    if iocs:
        base_prompt += "\n\n## Indicateurs de Compromission (IOCs) associés:\n"
        base_prompt += "\n".join(f"- {ioc}" for ioc in iocs)

    return base_prompt.format(text=text)
