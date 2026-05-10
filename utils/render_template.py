import os
from jinja2 import Environment, FileSystemLoader, select_autoescape

_env = Environment(
    loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), "..", "templates")),
    autoescape=select_autoescape(["html"]),
)


def render_stream_page(context: dict) -> str:
    template = _env.get_template("stream.html")
    return template.render(**context)


def render_dl_page(context: dict) -> str:
    template = _env.get_template("dl.html")
    return template.render(**context)
