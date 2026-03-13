import al
import typer
from al.plugins import load_plugins

app = typer.Typer()

for name, plugin_app in load_plugins(al):
    app.add_typer(plugin_app, name=name)


if __name__ == "__main__":
    app()
