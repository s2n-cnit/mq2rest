from typing import Dict, Self

import yaml
from log import logger


class Config:
    def __init__(self: Self) -> None:
        self.path = None
        self._data = {}

    def from_path(self: Self, path: str) -> Self:
        self.path = path
        try:
            with open(self.path, 'r') as f:
                self._data = yaml.safe_load(f) or {}  # Handle empty YAML files
        except FileNotFoundError:
            logger.error(f"Configuration file '{self.path}' not found.")
            self._data = {}
        except yaml.YAMLError as e:
            logger.error(f"parsing YAML file '{self.path}': {e}")
            self._data = {}
        return self

    def from_data(self: Self, data: dict) -> Self:
        self._data = data
        return self

    def get(self: Self, key: str, default: str = None, error_msg: bool = False) -> any:
        out = self._data.get(key, default)
        if error_msg and out is None:
            logger.error(f"{key} not defined in config {self.path}")
        if isinstance(out, dict):
            return Config().from_data(out)
        else:
            return out
