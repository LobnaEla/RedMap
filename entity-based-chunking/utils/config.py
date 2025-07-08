import yaml
import os
from dotenv import load_dotenv

def load_config(config_path: str = "config.yaml") -> dict:
    load_dotenv()
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return config
