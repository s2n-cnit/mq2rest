from typing import Any, Dict, Self

import yaml
from log import logger


class Config:
    """
    A class to load configuration parameters from a YAML file.
    """
    def __init__(self: Self, path: str = "config.yaml") -> None:
        """
        Initializes the Config class and loads data from the specified YAML file.

        Args:
            path (str, optional): The path to the YAML configuration file.
                                  Defaults to "config.yaml".
        """
        self.path = path
        self._data = self._load_config()

    def _load_config(self: Self) -> Dict:
        """
        Loads data from the YAML configuration file.

        Returns:
            dict: A dictionary containing the configuration data.
                  Returns an empty dictionary if the file is not found or an error occurs.
        """
        try:
            with open(self.path, 'r') as f:
                return yaml.safe_load(f) or {}  # Handle empty YAML files
        except FileNotFoundError:
            logger.error(f"Configuration file '{self.path}' not found.")
            return {}
        except yaml.YAMLError as e:
            logger.error(f"parsing YAML file '{self.path}': {e}")
            return {}

    def get(self: Self, key: str, default: Any = None) -> Any:
        """
        Retrieves a configuration value based on the key.

        Args:
            key (str): The key of the configuration parameter.
            default (any, optional): The value to return if the key is not found.
                                     Defaults to None.

        Returns:
            any: The configuration value associated with the key, or the default value
                 if the key is not found.
        """
        return self.get(key, default)

    def __getitem__(self: Self, key: str) -> Any:
        """
        Allows accessing configuration values using dictionary-like syntax (e.g., config['my_setting']).

        Args:
            key (str): The key of the configuration parameter.

        Returns:
            any: The configuration value associated with the key.

        Raises:
            KeyError: If the key is not found in the configuration.
        """
        if key not in self._data:
            raise KeyError(f"'{key}' not found in configuration file '{self.path}'.")
        return self._data[key]

    def __contains__(self: Self, key: str) -> bool:
        """
        Checks if a key exists in the configuration.

        Args:
            key (str): The key to check.

        Returns:
            bool: True if the key exists, False otherwise.
        """
        return key in self._data

    def get_section(self: Self, section_name: str, default: Dict = None) -> Dict:
        """
        Retrieves a specific section (a nested dictionary) from the configuration.

        Args:
            section_name (str): The name of the section.
            default (dict, optional): The dictionary to return if the section is not found.
                                      Defaults to None.

        Returns:
            dict: The configuration section as a dictionary, or the default value
                  if the section is not found.
        """
        return self._data.get(section_name, default)

    def all(self: Self) -> Dict:
        """
        Returns the entire configuration data as a dictionary.

        Returns:
            dict: The entire configuration data.
        """
        return self._data
