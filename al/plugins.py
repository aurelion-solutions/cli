import importlib
import pkgutil


def load_plugins(package):
    plugins = []

    for _, name, _ in pkgutil.iter_modules(package.__path__):
        try:
            module = importlib.import_module(f"{package.__name__}.{name}.cli")
        except ModuleNotFoundError:
            continue  # Skip modules without cli (e.g. client.py)
        if hasattr(module, "app"):
            plugins.append((name, module.app))

    return plugins
