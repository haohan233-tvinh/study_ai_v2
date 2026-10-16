"""Contracts that must survive moving V2 away from the original workspace."""
import json
import importlib.util
import os
from pathlib import Path
import subprocess
import sys

APP = Path(__file__).resolve().parents[1]
WORKSPACE = APP.parent


def test_default_solver_is_deep_learning_without_launcher_environment():
    env = dict(os.environ)
    env.pop('STUDY_AI_PROFILE', None)
    code = ('from clipboard_solver import ExamSolver; '
            's=ExamSolver(); '
            'assert s.settings["course"]=="deep_learning"; '
            'assert s.dl_pipeline is not None; s.close()')
    subprocess.run([sys.executable, '-c', code], cwd=APP, env=env,
                   check=True, capture_output=True, text=True, timeout=15)


def test_shipped_profiles_resolve_to_complete_assets_inside_this_workspace():
    for profile in ('settings.json', 'settings.deep_learning.json', 'settings.web.json'):
        settings = json.loads((APP / profile).read_text(encoding='utf-8'))
        for key in ('model', 'mmproj', 'server', 'knowledge'):
            if settings.get(key):
                path = (APP / settings[key]).resolve()
                assert path.is_relative_to(WORKSPACE), (profile, key, path)
                assert path.is_file(), (profile, key, path)


def test_backend_setup_preserves_course_without_v1_root_settings(tmp_path):
    spec = importlib.util.spec_from_file_location('v2_setup_assets', WORKSPACE / 'setup_assets.py')
    installer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(installer)
    app = tmp_path / 'fast_v2'
    app.mkdir()
    for name in ('settings.json', 'settings.deep_learning.json', 'settings.web.json'):
        (app / name).write_text(json.dumps({'model': 'keep-local.gguf', 'course': 'deep_learning'}))
    installer.set_backend('cpu', tmp_path)
    for name in ('settings.json', 'settings.deep_learning.json', 'settings.web.json'):
        settings = json.loads((app / name).read_text())
        assert settings['course'] == 'deep_learning'
        assert settings['model'] == 'keep-local.gguf'
        assert settings['server'] == '../runtime/cpu/llama-server.exe'
        assert settings['device'] == 'CPU'
