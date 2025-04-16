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
        logger.info(f"Translating from {template} using {data}")
        out = template.copy()
        if "value" in template:
            if "Value" in data:
                out["value"] = template["value"].replace("<VALUE>", str(data["Value"]))
            else:
                out["value"] = template["value"].replace("<VALUE>", str(data["Status"]))
        elif "Value" in template:
            out["Value"] = get_float(template["Value"].replace("<VALUE>", data["value"]))
        elif "Status" in template:
            out["Status"] = get_float(template["Status"].replace("<VALUE>", data["value"]))
        else:
            logger.warning(f"Unknown payload: {template}")
        logger.info(f"Translated {data} to {out}")
        return json.dumps(out)
    except KeyError as ke:
        logger.error(f"Translate {data} to {out} using {template} [{ke}]")
    except Exception as e:
        logger.error(e)
