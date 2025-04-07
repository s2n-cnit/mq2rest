from jinja2 import Environment


def Template(template_string):
    env = Environment(variable_start_string='{', variable_end_string='}',
                      block_start_string='{%', block_end_string='%}',
                      comment_start_string='{#', comment_end_string='#}')
    return env.from_string(template_string)
