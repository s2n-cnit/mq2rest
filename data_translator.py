import json
from typing import Dict

from jinja2 import Environment, Template
from parse import parse


def __template(template_string) -> Template:
    env = Environment(variable_start_string='{', variable_end_string='}',
                      block_start_string='{%', block_end_string='%}',
                      comment_start_string='{#', comment_end_string='#}')
    return env.from_string(template_string)


def translate(data: Dict, template_in: Dict, template_out: Dict) -> str:
    data_in = json.dumps(data)
    body_in = json.dumps(template_in)
    body_out = json.dumps(template_out)

    r = parse(body_in, data_in)
    return Template(body_out).render(r.named)
