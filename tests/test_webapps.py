import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def _load_app(module_path: Path):
    spec = importlib.util.spec_from_file_location(module_path.stem, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module.app


def test_health_endpoint_is_200_for_all_services():
    service_paths = [
        ROOT / "webapps" / "webapp-main" / "app.py",
        ROOT / "webapps" / "webapp-auth" / "app.py",
        ROOT / "webapps" / "webapp-payment" / "app.py",
    ]

    for path in service_paths:
        app = _load_app(path)
        client = app.test_client()
        response = client.get("/health")
        assert response.status_code == 200
        payload = response.get_json()
        assert payload["status"] == "healthy"


def test_toggle_health_switches_between_200_and_500():
    service_paths = [
        ROOT / "webapps" / "webapp-main" / "app.py",
        ROOT / "webapps" / "webapp-auth" / "app.py",
        ROOT / "webapps" / "webapp-payment" / "app.py",
    ]

    for path in service_paths:
        app = _load_app(path)
        client = app.test_client()

        first_toggle = client.get("/toggle-health")
        assert first_toggle.status_code == 200
        assert first_toggle.get_json()["toggled_to"] == "unhealthy"

        unhealthy = client.get("/health")
        assert unhealthy.status_code == 500

        second_toggle = client.get("/toggle-health")
        assert second_toggle.status_code == 200
        assert second_toggle.get_json()["toggled_to"] == "healthy"

        healthy = client.get("/health")
        assert healthy.status_code == 200
