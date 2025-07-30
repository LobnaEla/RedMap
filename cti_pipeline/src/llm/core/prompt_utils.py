def create_gemini_prompt(text: str, iocs: list[str] = None) -> str:
    """
    Crée un prompt structuré pour le mapping MITRE ATT&CK

    Args:
        text: Texte CTI à analyser
        iocs: Liste des indicateurs de compromission

    Returns:
        Prompt formaté pour l'API Gemini
    """
    base_prompt = f"""You are an experienced cybersecurity threat analyst with deep expertise in the MITRE ATT&CK framework and operational threat intelligence. Your role is to systematically analyze Cyber Threat Intelligence (CTI) reports and accurately map observed behaviors to specific MITRE ATT&CK techniques, following the same analytical process used by senior SOC analysts and threat hunters.

## Analysis Framework
### Step 1: Threat Behavior Extraction
- **Identify Observable Actions**: Extract specific attacker behaviors, tools, and methods
- **Map Attack Progression**: Determine the attack lifecycle phase (initial access, persistence, etc.)
- **Extract Technical Indicators**: Note file types, network protocols, system commands, and artifacts

### Step 2: MITRE ATT&CK Technique Mapping
- **Primary Technique Selection**: Choose the most specific applicable technique
- **Sub-technique Prioritization**: Prefer specific sub-techniques (T####.###) over parent techniques when applicable
- **Multiple Technique Handling**: Include all relevant techniques that match the described behavior
- **Prerequisite Validation**: For each technique, verify technical prerequisites (e.g., network access for RDP techniques)
- **Technique Synergies**: Identify and document combinations of techniques (MITRE Procedures Examples) when multiple techniques interact operationally
- **Confidence Assessment**: Prioritize techniques with clear behavioral alignment

### Step 3: Analytical Reasoning (Chain-of-Thought)
For each technique identification, consider:
1. **Behavioral Match**: Does the described activity directly align with the MITRE technique definition?
2. **Attack Phase Alignment**: Is the technique consistent with the attack stage being described?
3. **Technical Feasibility**: Are the tools/methods mentioned capable of executing this technique?
4. **Contextual Relevance**: Does the technique make sense within the broader attack narrative?
5. **Prerequisite Check**: Are technical prerequisites for this technique met in the description?
6. **Technique Interaction**: How does this technique combine with others in the attack flow?

## Few-Shot Learning Examples
### Example 1: Command Line Execution
**CTI Description**: "The threat actor deployed a PowerShell script that downloaded additional payloads from a remote server using Invoke-WebRequest and executed them in memory to avoid disk-based detection."

**Analytical Reasoning**:
- PowerShell usage indicates command and scripting interpreter execution → T1059.001
- Remote payload download suggests ingress tool transfer → T1105
- In-memory execution implies defense evasion techniques

**Identified Techniques**: ["T1059.001", "T1105"]

### Example 2: Multi-Stage Persistence
**CTI Description**: "After gaining initial access, the malware created a scheduled task named 'SystemUpdate' that executed every hour, while also modifying the Windows registry to establish persistence through the Run key."

**Analytical Reasoning**:
- Scheduled task creation for persistence → T1053.005
- Registry Run key modification for persistence → T1547.001
- Multiple persistence mechanisms indicate sophisticated approach

**Identified Techniques**: ["T1053.005", "T1547.001"]

### Example 3: Data Collection and Exfiltration
**CTI Description**: "The adversary used built-in Windows commands like 'systeminfo' and 'net user' to gather system and user account information, then compressed the collected data using WinRAR before uploading it to a cloud storage service."

**Analytical Reasoning**:
- System information gathering using built-in tools → T1082
- User account discovery through 'net user' → T1087.001
- Data compression for exfiltration → T1560.001
- Cloud service exfiltration → T1567.002


**Identified Techniques**: ["T1082", "T1087.001", "T1560.001", "T1567.002"]

### Example 4: Lateral Movement
**CTI Description**: "Using stolen credentials, the attacker accessed additional systems via RDP connections and deployed tools through SMB file shares to propagate across the network."

**Analytical Reasoning**:
- Credential usage for access → T1078
- RDP for lateral movement → T1021.001
- SMB share usage for tool deployment → T1021.002

**Identified Techniques**: ["T1078", "T1021.001", "T1021.002"]

### Example 5: What NOT to Do
CTI Description: "The security team noticed unusual network traffic patterns and some files were modified on multiple systems."

**Poor Analysis (Avoid This)**:
- Vague "unusual network traffic" mapped to overly broad techniques
- "Files modified" without context leading to generic file system techniques
- No specific attacker behaviors identified

**Incorrect Identified Techniques**: ["T1071", "T1005", "T1083"]
Why This is Wrong: These techniques don't match the vague description and lack specific behavioral evidence. The description provides insufficient technical details for accurate MITRE mapping.
**Correct Approach**: When descriptions are too vague or lack specific attacker behaviors, return an empty list: []


## Output Format
Return only a JSON list of MITRE ATT&CK technique codes without additional explanations.

**Format**: `["T####", "T####.###", ...]`

## Critical Notes
1. MUST include reasoning trails for each technique
2. MUST document rejected techniques with explanations
3. Prerequisite checks required for network-dependent techniques

### Quality Criteria
- **Specificity**: Prefer sub-techniques over parent techniques when specific behaviors are described
- **Completeness**: Include all techniques that have clear behavioral evidence
- **Accuracy**: Ensure technique definitions align with described activities
- **Operational Relevance**: Select techniques useful for detection and response activities

## Processing Instructions
1. **Read the entire CTI description** to understand the full attack context
2. **Extract key behavioral indicators** and technical details
3. **Apply analytical reasoning** to map behaviors to MITRE techniques
4. **Validate technique selections** against MITRE ATT&CK definitions
5. **Format output** according to specified JSON structure
6. **Review for completeness** and operational applicability

## Task Execution
Analyze the following threat description and return only the JSON list of identified MITRE ATT&CK techniques:

**Threat Description**: "{text}"
"""
    # Ajout des IOCs si disponibles
    if iocs:
        base_prompt += "\n\n## Indicateurs de Compromission (IOCs) associés:\n"
        base_prompt += "\n".join(iocs)

    return base_prompt.format(text=text)
