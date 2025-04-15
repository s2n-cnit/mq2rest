import json
from typing import Dict

from log import logger


def translate(data: Dict | str, template: Dict) -> str:
    if isinstance(data, str):
        data = json.loads(data)
    try:
        template["value"] = str(data["value"])
        logger.info(f"in: {data} out: {template}")
        return json.dumps(template)
    except Exception as e:
        logger.error(e)
