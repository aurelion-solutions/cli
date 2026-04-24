"""Smoke test — verifies that the plugin loader discovers all expected plugins."""

import al
from al.plugins import load_plugins


def test_all_expected_plugins_loaded() -> None:
    plugins = load_plugins(al)
    plugin_names = {name for name, _ in plugins}

    # Phase 13 Step 17 new plugins
    assert "sod" in plugin_names, "sod plugin not discovered"
    assert "scan" in plugin_names, "scan plugin not discovered"
    assert "findings" in plugin_names, "findings plugin not discovered"
    assert "feedback" in plugin_names, "feedback plugin not discovered"


def test_plugin_apps_are_typer_instances() -> None:
    import typer

    plugins = load_plugins(al)
    plugin_map = {name: app for name, app in plugins}

    for name in ("sod", "scan", "findings", "feedback"):
        assert name in plugin_map, f"{name} missing from plugin map"
        assert isinstance(plugin_map[name], typer.Typer), (
            f"{name} plugin app is not a typer.Typer instance"
        )
