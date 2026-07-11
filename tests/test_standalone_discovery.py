import sys
from pathlib import Path

def test_user_plugin_discovery_loads_jiuwenmemory(tmp_path, monkeypatch):
    repo_root = Path(__file__).resolve().parents[1]
    hermes_repo = Path(__import__('os').environ.get('HERMES_AGENT_REPO', '/home/wzk/.hermes/hermes-agent'))
    for path in (str(hermes_repo), str(repo_root)):
        if path not in sys.path:
            sys.path.insert(0, path)

    hermes_home = tmp_path / '.hermes'
    plugin_dir = hermes_home / 'plugins' / 'jiuwenmemory'
    plugin_dir.parent.mkdir(parents=True)
    plugin_dir.symlink_to(repo_root, target_is_directory=True)
    monkeypatch.setenv('HERMES_HOME', str(hermes_home))

    from plugins.memory import discover_memory_providers, load_memory_provider

    providers = {name: (desc, available) for name, desc, available in discover_memory_providers()}
    assert 'jiuwenmemory' in providers
    provider = load_memory_provider('jiuwenmemory')
    assert provider is not None
    assert provider.name == 'jiuwenmemory'
