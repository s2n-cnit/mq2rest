import os

import yaml


class Config:
    """
    A class to load configuration parameters from a YAML file.
    """
    def __init__(self, config_file="config.yaml"):
        """
        Initializes the Config class and loads data from the specified YAML file.

        Args:
            config_file (str, optional): The path to the YAML configuration file.
                                         Defaults to "config.yaml".
        """
        self.config_file = config_file
        self._config_data = self._load_config()

    def _load_config(self):
        """
        Loads data from the YAML configuration file.

        Returns:
            dict: A dictionary containing the configuration data.
                  Returns an empty dictionary if the file is not found or an error occurs.
        """
        try:
            with open(self.config_file, 'r') as f:
                return yaml.safe_load(f) or {}  # Handle empty YAML files
        except FileNotFoundError:
            print(f"Error: Configuration file '{self.config_file}' not found.")
            return {}
        except yaml.YAMLError as e:
            print(f"Error parsing YAML file '{self.config_file}': {e}")
            return {}

    def get(self, key, default=None):
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
        return self._config_data.get(key, default)

    def __getitem__(self, key):
        """
        Allows accessing configuration values using dictionary-like syntax (e.g., config['my_setting']).

        Args:
            key (str): The key of the configuration parameter.

        Returns:
            any: The configuration value associated with the key.

        Raises:
            KeyError: If the key is not found in the configuration.
        """
        if key not in self._config_data:
            raise KeyError(f"'{key}' not found in configuration file '{self.config_file}'.")
        return self._config_data[key]

    def __contains__(self, key):
        """
        Checks if a key exists in the configuration.

        Args:
            key (str): The key to check.

        Returns:
            bool: True if the key exists, False otherwise.
        """
        return key in self._config_data

    def get_section(self, section_name, default=None):
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
        return self._config_data.get(section_name, default)

    def all(self):
        """
        Returns the entire configuration data as a dictionary.

        Returns:
            dict: The entire configuration data.
        """
        return self._config_data

# Example Usage:

# 1. Create a YAML configuration file (e.g., config.yaml) in the same directory:
"""
http:
  base_url: "http://api.example.com"
  timeout: 10
  headers:
    Content-Type: "application/json"
mqtt:
  broker_address: "broker.example.com"
  port: 1883
  topics:
    publish: "sensor/data"
    subscribe: "commands/#"
database:
  host: "localhost"
  port: 5432
  username: "user"
  password: "secret"
"""

if __name__ == "__main__":
    # Create an instance of the Config class (it will load from config.yaml by default)
    config = Config()

    # Access configuration values using the get() method with a default value
    http_base_url = config.get("http:base_url")
    http_timeout = config.get("http:timeout", 5)  # Default timeout if not found
    non_existent_setting = config.get("non_existent", "default_value")

    print(f"HTTP Base URL: {http_base_url}")
    print(f"HTTP Timeout: {http_timeout}")
    print(f"Non-existent setting: {non_existent_setting}")

    print("-" * 20)

    # Access configuration values using dictionary-like syntax
    try:
        mqtt_broker = config["mqtt:broker_address"]
        mqtt_publish_topic = config["mqtt:topics:publish"]
        # Trying to access a non-existent key will raise a KeyError
        # non_existent = config["does_not_exist"]
    except KeyError as e:
        print(f"Error: {e}")
    else:
        print(f"MQTT Broker Address: {mqtt_broker}")
        print(f"MQTT Publish Topic: {mqtt_publish_topic}")

    print("-" * 20)

    # Check if a key exists
    if "database" in config:
        database_host = config["database:host"]
        print(f"Database Host: {database_host}")

    print("-" * 20)

    # Get an entire section
    mqtt_config = config.get_section("mqtt")
    if mqtt_config:
        print("MQTT Configuration:")
        print(f"  Broker Address: {mqtt_config.get('broker_address')}")
        print(f"  Port: {mqtt_config.get('port')}")
        print(f"  Topics: {mqtt_config.get('topics')}")

    print("-" * 20)

    # Get all configuration data
    all_config = config.all()
    print("All Configuration Data:")
    import json
    print(json.dumps(all_config, indent=2))

    print("-" * 20)

    # You can also specify a different configuration file when creating the instance
    # another_config = Config("another_config.yaml")
    # print(f"Config from another file: {another_config.get('some_setting')}")
