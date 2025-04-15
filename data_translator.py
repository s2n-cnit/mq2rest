import json
from typing import Dict

from log import logger


def get_float(s: str) -> float | str:
    try:
        return float(s)
    except ValueError:
        return s


def translate(data: Dict | str, template: Dict) -> str:
    if isinstance(data, str):
        data = json.loads(data)
    try:
        if "value" in template:
            if "Value" in data:
                template["value"] = template["value"].replace("<VALUE>", str(data["Value"]))
            else:
                template["value"] = template["value"].replace("<VALUE>", str(data["Status"]))
        elif "Value" in template:
            template["Value"] = get_float(template["value"].replace("<VALUE>", data["value"]))
        elif "Status" in template:
            template["Status"] = get_float(template["value"].replace("<VALUE>", data["value"]))
        else:
            logger.warning(f"Unknown payload: {template}")
        logger.info(f"in: {data} out: {template}")
        return json.dumps(template)
    except Exception as e:
        logger.error(e)
