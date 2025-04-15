import json
from typing import Dict

from log import logger


def translate(data: Dict | str, template: Dict) -> str:
    if isinstance(data, str):
        data = json.loads(data)
    try:
        if "value" in template:
            template["value"] = template["value"].replace("<VALUE>", str(data["Value"]))
        elif "Value" in template:
            template["Value"] = float(template["value"].replace("<VALUE>", data["value"]))
        else:
            logger.warning(f"Unknown payload: {template}")
        logger.info(f"in: {data} out: {template}")
        return json.dumps(template)
    except Exception as e:
        logger.error(e)
