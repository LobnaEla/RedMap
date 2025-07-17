"""
Preservation logic
"""

from typing import Set
from .patterns import PatternManager

class PreservationManager:
    """Manages what content should be preserved during anonymization"""
    
    def __init__(self):
        self.technical_terms = self._load_technical_terms()
        self.government_domains = self._load_government_domains()
        self.agency_names = self._load_agency_names()
        self.facility_types = self._load_facility_types()
        self.classification_terms = self._load_classification_terms()
        self.pattern_manager = PatternManager()
    
    def _load_technical_terms(self) -> Set[str]:
        """Load technical terms that should be preserved"""
        return {
            # Operating Systems & Software
            'windows', 'linux', 'macos', 'android', 'ios', 'ubuntu', 'debian',
            'microsoft', 'office', 'chrome', 'firefox', 'safari', 'edge',
            'adobe', 'flash', 'java', 'python', 'powershell', 'cmd',
            
            # Security Tools & Products
            'nmap', 'metasploit', 'burp', 'wireshark', 'nessus', 'qualys',
            'splunk', 'elk', 'siem', 'ids', 'ips', 'firewall', 'antivirus',
            
            # Malware & Threat Terms
            'apt', 'trojan', 'ransomware', 'backdoor', 'rootkit', 'keylogger',
            'botnet', 'ddos', 'phishing', 'spearphishing', 'watering hole',
            
            # CTI & MITRE Terms
            'mitre', 'attack', 'tactic', 'technique', 'procedure', 'ttp',
            'indicator', 'ioc', 'compromise', 'attribution', 'campaign',
            
            # Cryptographic Terms
            'aes', 'rsa', 'sha', 'md5', 'ssl', 'tls', 'pki', 'certificate',
            'encryption', 'decryption', 'hash', 'signature', 'algorithm',
            
            # Network Terms
            'tcp', 'udp', 'http', 'https', 'ftp', 'smtp', 'dns', 'dhcp',
            'vpn', 'proxy', 'gateway', 'router', 'switch', 'api', 'endpoint',
            
            # File Extensions
            'exe', 'dll', 'pdf', 'doc', 'docx', 'zip', 'rar', 'tar', 'gz',
            'bin', 'iso', 'img', 'bat', 'ps1', 'sh'
        }
    
    def _load_government_domains(self) -> Set[str]:
        """Load government domains that should be preserved"""
        return {
            '.gov', '.mil', '.fed.us', '.state.us', '.edu',
            'nsa.gov', 'fbi.gov', 'dhs.gov', 'cisa.gov', 'cyber.mil',
            'cert.org', 'mitre.org', 'nist.gov'
        }
    
    def _load_agency_names(self) -> Set[str]:
        """Load agency names that should be preserved"""
        return {
            'cisa', 'cybersecurity and infrastructure security agency',
            'department of homeland security', 'dhs',
            'federal bureau of investigation', 'fbi',
            'national security agency', 'nsa',
            'central intelligence agency', 'cia',
            'department of energy', 'doe',
            'department of defense', 'dod',
            'national institute of standards and technology', 'nist',
            'computer emergency readiness team', 'cert', 'us-cert'
        }
    
    def _load_facility_types(self) -> Set[str]:
        """Load facility types that should be preserved"""
        return {
            'nuclear facility', 'nuclear plant', 'nuclear reactor',
            'power plant', 'power station', 'electrical grid', 'power grid',
            'water treatment plant', 'water facility', 'wastewater',
            'oil refinery', 'gas pipeline', 'petroleum facility',
            'chemical plant', 'manufacturing facility',
            'data center', 'telecommunications', 'internet backbone',
            'transportation hub', 'airport', 'seaport', 'railway',
            'financial institution', 'bank', 'critical infrastructure'
        }
    
    def _load_classification_terms(self) -> Set[str]:
        """Load classification terms that should be preserved"""
        return {
            'unclassified', 'cui', 'confidential', 'secret', 'top secret',
            'sci', 'sap', 'noforn', 'fouo', 'official', 'restricted',
            'clearance', 'classification', 'sensitive'
        }
    
    def should_preserve_text(self, text: str) -> bool:
        text_lower = text.lower()

        if any(term in text_lower for term in self.technical_terms):
            return True

        if any(domain in text_lower for domain in self.government_domains):
            return True

        if any(agency in text_lower for agency in self.agency_names):
            return True

        if any(facility in text_lower for facility in self.facility_types):
            return True

        if any(term in text_lower for term in self.classification_terms):
            return True

        if any(pattern in text_lower for pattern in self.custom_preserve_patterns):
            return True

        return False
    
    def is_ioc(self, text: str) -> bool:
        for pattern_name in ['ip_address', 'hash_md5', 'hash_sha1', 'hash_sha256', 'url', 'domain']:
            if self.pattern_manager.get_pattern(pattern_name).fullmatch(text.strip()):
                return True
        return False