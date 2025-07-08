import yaml
import os
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

def load_config(config_path: str = "config.yaml") -> dict:
    """Load configuration from YAML file with environment variable support."""
    load_dotenv()
    
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        logger.debug(f"Configuration loaded from {config_path}")
        return config
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML configuration: {e}")


def validate_config(config: dict) -> None:
    """Validate required configuration parameters."""
    required_keys = {
        "groq": ["api_url", "model"],
        "prompts": ["ioc_extraction"]
    }
    
    for section, keys in required_keys.items():
        if section not in config:
            raise ValueError(f"Missing configuration section: {section}")
        
        for key in keys:
            if key not in config[section]:
                raise ValueError(f"Missing configuration key: {section}.{key}")
    
    # Validate API key availability
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable not set")
    
    logger.debug("Configuration validation passed")
