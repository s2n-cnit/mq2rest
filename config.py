from typing import Dict, Self

import yaml
from log import logger


class Config:
    def __init__(self: Self, path: str = "config.yaml") -> None:
        self.path = path
        self._data = self._load()

    def _load(self: Self) -> Dict:
        try:
            with open(self.path, 'r') as f:
                return yaml.safe_load(f) or {}  # Handle empty YAML files
        except FileNotFoundError:
            logger.error(f"Configuration file '{self.path}' not found.")
            return {}
        except yaml.YAMLError as e:
            logger.error(f"parsing YAML file '{self.path}': {e}")
            return {}

    def get(self: Self, key: str, default: str = None, error_msg: bool = False):
        out = self._data.get(key, default)
        if error_msg and out is None:
            logger.error(f"{key} not defined in config {self.path}")
