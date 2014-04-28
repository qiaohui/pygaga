import os
from jinja2 import Environment
from jinja2 import FileSystemLoader
import web

def file_env(file_path):
    return Environment(loader = FileSystemLoader(os.path.join(file_path, 'templates'), encoding='utf8'), auto_reload=True)

def render_to_string(env, template_name, context):
    template = env.get_template(template_name)
    return template.render(context)

def render_html(env, template_name, context):
    web.header("Content-Type", "text/html; charset=utf-8")
    return render_to_string(env, template_name, context)
