import json
from typing import Self

import requests
from config import Config
from log import logger

headers = {
    "Content-Type": "application/json"
}


class RESTHTTPClient:
    def __init__(self: Self, config: Config) -> None:
        self.config = config.get("rest")

    def run(self: Self, endpoint: str, method: str, data: any, callback: callable) -> None:
        try:
            match method.upper():
                case "GET": r = requests.get
                case "POST": r = requests.post
                case "PUT": r = requests.put
                case "DELETE": r = requests.delete
                case _:
                    logger.error(f"Unsupported REST HTTP method '{method}' for URL: {endpoint}")
                    return
            url = self.config.get("base_url") + endpoint
            logger.info(f"HTTP {method.upper()} Request to {url}: {data}")
            resp = r(url, data=data, headers=headers)
            resp.raise_for_status()  # Raise an exception for bad status codes
            logger.info(f"HTTP {method.upper()} Response from {url}: {resp.content}")
            callback(data=resp.json())
        except requests.exceptions.RequestException as e:
            logger.error(f"REST HTTP request to '{url}' failed: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"Decoding JSON response from '{url}': {e}")
        except Exception as e:
            logger.error(f"Unexpected error occurred: {e}")
