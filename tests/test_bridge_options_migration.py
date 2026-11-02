"""Explicit existing settings must override changed upstream defaults."""
import json


def test_existing_options_override_new_defaults(bridge_module, tmp_path):
    existing = {
        'bridge_ip': '', 'cloud_host': 'synthetic.invalid', 'forward_to_cloud': True,
        'upstream_dns': '', 'dns_port': 0, 'cloud_dns': ['1.1.1.1', '1.0.0.1'],
        'http_port': 80, 'passthrough_url': '', 'api_port': 8642, 'log_level': 'info',
    }
    path = tmp_path / 'options.json'
    path.write_text(json.dumps(existing))
    loaded = bridge_module.load_options(path)
    assert {k: loaded[k] for k in existing} == existing
    assert loaded['state_file'] == '/data/recipes.json'
    assert loaded['diagnostics_enabled'] is False
    assert loaded['diagnostics_max_file_mb'] == 8
    assert loaded['diagnostics_files'] == 4
    assert json.loads(path.read_text()) == existing
