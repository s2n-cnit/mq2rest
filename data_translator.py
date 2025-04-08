import json
from typing import Dict

from log import logger


def translate(data: Dict, template: Dict) -> str:
    if "value" in data:
        template["e"][0]["v"] = data["value"]
    else:
        template["value"] = data["e"][0]["v"]
    logger.info(f"in: {data} out: {template}")
    return json.dumps(template)
