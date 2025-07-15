"""
Main anonymization logic
"""

from typing import Dict, Any, List
from .config import AnonymizationConfig
from ...utils.patterns import PatternManager
from ...utils.preservers import PreservationManager
from .replacers import ReplacementManager

class TextAnonymizer:
    """
    Main anonymization class that coordinates all anonymization operations
    """
    
    def __init__(self, config: AnonymizationConfig = None):
        self.config = config or AnonymizationConfig()
        self.pattern_manager = PatternManager()
        self.preservation_manager = PreservationManager(self.config)
        self.replacement_manager = ReplacementManager()
        self.ioc_preservation_map: Dict[str, str] = {}
        
        # Load malware names from Malpedia for preservation
        self.malware_names = self.pattern_manager.get_malware_names()
        if self.malware_names:
            print(f"Loaded {len(self.malware_names)} malware names from Malpedia for preservation")
        else:
            print("Using built-in malware preservation list")
    
    def _preserve_iocs(self, text: str) -> str:
        """Preserve IoCs by replacing them with placeholders"""
        if not self.config.preserve_iocs:
            return text
        
        try:
            self.ioc_preservation_map.clear()
            
            # Preserve technical indicators
            ioc_patterns = [
                'ip_address', 'hash_md5', 'hash_sha1', 'hash_sha256', 'hash_sha512',
                'url', 'domain', 'cve_id', 'malware_name'
            ]            
            for pattern_name in ioc_patterns:
                pattern = self.pattern_manager.get_pattern(pattern_name)
                if pattern:
                    matches = pattern.findall(text)
                    for i, match in enumerate(matches):
                        placeholder = f"__IOC_{pattern_name.upper()}_{i}__"
                        self.ioc_preservation_map[placeholder] = match
                        text = text.replace(match, placeholder)
            
            # Preserve dynamically loaded malware names from Malpedia
            if self.malware_names:
                for i, malware_name in enumerate(self.malware_names):
                    if malware_name.lower() in text.lower():
                        # Case-insensitive replacement while preserving original case
                        import re
                        pattern = re.compile(re.escape(malware_name), re.IGNORECASE)
                        matches = pattern.findall(text)
                        for j, match in enumerate(matches):
                            placeholder = f"__MALWARE_{i}_{j}__"
                            self.ioc_preservation_map[placeholder] = match
                            text = pattern.sub(placeholder, text, count=1)
            
            return text
            
        except Exception as e:
            print(f"Error preserving IoCs: {e}")
            return text
    
    def _restore_iocs(self, text: str) -> str:
        """Restore preserved IoCs"""
        try:
            for placeholder, ioc_value in self.ioc_preservation_map.items():
                text = text.replace(placeholder, ioc_value)
            return text
        except Exception as e:
            print(f"Error restoring IoCs: {e}")
            return text
    
    def _anonymize_emails(self, text: str) -> str:
        """Anonymize email addresses"""
        if not self.config.anonymize_emails:
            return text
        
        def replace_email(match):
            email = match.group(0)
            
            # Check if should be preserved
            if self.preservation_manager.should_preserve_text(email):
                return email
            
            # Check if it's an IoC
            if self.preservation_manager.is_ioc(email):
                return email
            
            return self.replacement_manager.generate_replacement(email, 'email')
        
        pattern = self.pattern_manager.get_pattern('email')
        if pattern:
            return pattern.sub(replace_email, text)
        return text
    
    def _anonymize_phones(self, text: str) -> str:
        """Anonymize phone numbers"""
        if not self.config.anonymize_phones:
            return text
        
        def replace_phone(match):
            phone = match.group(0)
            
            # Check if should be preserved
            if self.preservation_manager.should_preserve_text(phone):
                return phone
            
            return self.replacement_manager.generate_replacement(phone, 'phone')
        
        pattern = self.pattern_manager.get_pattern('phone')
        if pattern:
            return pattern.sub(replace_phone, text)
        return text
    
    def _anonymize_names(self, text: str) -> str:
        """Anonymize person names"""
        if not self.config.anonymize_names:
            return text
        
        def replace_name(match):
            name = match.group(0)
            
            # Check if should be preserved
            if self.preservation_manager.should_preserve_text(name):
                return name
            
            # Check length constraints
            if len(name) < self.config.min_name_length or len(name) > self.config.max_name_length:
                return name
            
            return self.replacement_manager.generate_replacement(name, 'name')
        
        # Process both basic names and names with titles
        for pattern_name in ['person_name', 'person_name_with_title']:
            pattern = self.pattern_manager.get_pattern(pattern_name)
            if pattern:
                text = pattern.sub(replace_name, text)
        
        return text
    
    def _anonymize_organizations(self, text: str) -> str:
        """Anonymize organization names"""
        def replace_organization(match):
            org = match.group(0)
            
            # Check if should be preserved
            if self.preservation_manager.should_preserve_text(org):
                return org
            
            return self.replacement_manager.generate_replacement(org, 'organization')
        
        pattern = self.pattern_manager.get_pattern('organization')
        if pattern:
            return pattern.sub(replace_organization, text)
        return text
    
    def _anonymize_sensitive_patterns(self, text: str) -> str:
        """Anonymize other sensitive patterns (SSN, credit cards, etc.)"""
        
        # SSN
        if self.config.anonymize_ssn:
            pattern = self.pattern_manager.get_pattern('ssn')
            if pattern:
                text = pattern.sub(lambda m: self.replacement_manager.generate_replacement(m.group(0), 'ssn'), text)
        
        # Credit cards
        if self.config.anonymize_credit_cards:
            pattern = self.pattern_manager.get_pattern('credit_card')
            if pattern:
                text = pattern.sub(lambda m: self.replacement_manager.generate_replacement(m.group(0), 'credit_card'), text)
        
        return text
    
    def _apply_custom_patterns(self, text: str) -> str:
        """Apply custom anonymization patterns"""
        for pattern_name, replacement in self.config.custom_anonymize_patterns.items():
            try:
                text = text.replace(pattern_name, replacement)
            except Exception as e:
                print(f"Error applying custom pattern {pattern_name}: {e}")
        
        return text
    
    def anonymize(self, text: str) -> str:
        """
        Main anonymization function that applies all anonymization steps
        """
        try:
            print("Starting text anonymization...")
            
            # Step 1: Preserve IoCs before processing
            text = self._preserve_iocs(text)
            
            # Step 2: Apply anonymization steps
            text = self._anonymize_emails(text)
            text = self._anonymize_phones(text)
            text = self._anonymize_names(text)
            text = self._anonymize_organizations(text)
            text = self._anonymize_sensitive_patterns(text)
            
            # Step 3: Apply custom patterns
            text = self._apply_custom_patterns(text)
            
            # Step 4: Restore preserved IoCs
            text = self._restore_iocs(text)
            
            print("Text anonymization completed successfully")
            return text
            
        except Exception as e:
            print(f"Error in text anonymization: {e}")
            # Try to restore IoCs even if anonymization failed
            try:
                text = self._restore_iocs(text)
            except:
                pass
            return text
    
    def get_anonymization_stats(self) -> Dict[str, Any]:
        """Get statistics about the anonymization process"""
        # Get malware stats from PatternManager
        malware_stats = self.pattern_manager.get_malware_stats()
        
        return {
            'config': {
                'preserve_iocs': self.config.preserve_iocs,
                'preserve_technical_terms': self.config.preserve_technical_terms,
                'anonymize_emails': self.config.anonymize_emails,
                'anonymize_names': self.config.anonymize_names,
            },
            'replacements': self.replacement_manager.get_replacement_stats(),
            'iocs_preserved': len(self.ioc_preservation_map),
            'malware_names_loaded': malware_stats.get('total_malware_names', 0),
            'malpedia_integration': malware_stats.get('malpedia_names', 0) > 0,
            'malware_stats': malware_stats
        }
