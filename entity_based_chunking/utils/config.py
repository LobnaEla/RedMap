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
    # Check for required top-level sections
    required_sections = ["llm", "prompts"]
    for section in required_sections:
        if section not in config:
            raise ValueError(f"Missing configuration section: {section}")
    
    # Validate LLM configuration
    llm_config = config["llm"]
    if "provider" not in llm_config:
        raise ValueError("Missing configuration key: llm.provider")
    
    provider = llm_config["provider"]
    if provider not in llm_config:
        raise ValueError(f"Missing configuration for provider: {provider}")
    
    # Validate provider-specific configuration
    provider_config = llm_config[provider]
    required_provider_keys = ["base_url", "model", "api_key_env"]
    for key in required_provider_keys:
        if key not in provider_config:
            raise ValueError(f"Missing configuration key: llm.{provider}.{key}")
    
    # Validate prompts section
    if "ioc_extraction" not in config["prompts"]:
        raise ValueError("Missing configuration key: prompts.ioc_extraction")
    
    # Validate API key availability
    api_key_env = provider_config["api_key_env"]
    api_key = os.getenv(api_key_env)
    if not api_key:
        raise ValueError(f"{api_key_env} environment variable not set")
    
    logger.debug("Configuration validation passed")
