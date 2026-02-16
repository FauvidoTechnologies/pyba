from pathlib import Path

import yaml

current_file = Path(__file__)


class ConfigFilePath:
    general = current_file.parent.parent / "config.yaml"
    extraction = current_file.parent.parent / "core/scripts/extractions/extraction_configs.yaml"


def load_config(config_type: str):
    """
    It currently supports two types of config files:

    1. `general` which points to the main config.yaml file
    2. `extraction` which points to the extraction_config.yaml file inside extraction_scripts/
    """
    try:
        config_path = getattr(ConfigFilePath, config_type)
    except AttributeError:
        raise ValueError(f"Invalid config type '{config_type}'")

    with open(config_path, "r") as f:
        return yaml.safe_load(f)
