import json
from typing import Dict

from log import logger


def translate(data: Dict | str, template: Dict) -> str:
    if isinstance(data, str):
        data = json.loads(data)
    try:
        if "value" in data:
            template["e"][0]["v"] = data["value"]
        else:
            template["value"] = str(data["e"][0]["v"])
        logger.info(f"in: {data} out: {template}")
        return json.dumps(template)
    except Exception as e:
        logger.error(e)
