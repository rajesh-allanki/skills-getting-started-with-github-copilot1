import copy
import pytest
from fastapi.testclient import TestClient

from src import app as app_module


ORIGINAL_ACTIVITIES = copy.deepcopy(app_module.activities)


@pytest.fixture(autouse=True)
def reset_activities():
    # reset the in-memory activities before each test
    app_module.activities.clear()
    app_module.activities.update(copy.deepcopy(ORIGINAL_ACTIVITIES))
    yield


@pytest.fixture()
def client():
    return TestClient(app_module.app)


def test_get_activities(client):
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    # basic sanity checks
    assert "Chess Club" in data
    assert isinstance(data["Chess Club"], dict)


def test_signup_and_unregister_flow(client):
    activity_name = "Basketball Team"
    email = "tester@example.com"

    # Ensure participant not already present
    resp = client.get("/activities")
    assert resp.status_code == 200
    assert email not in resp.json()[activity_name]["participants"]

    # Sign up
    resp = client.post(f"/activities/{activity_name}/signup?email={email}")
    assert resp.status_code == 200
    assert resp.json()["message"] == f"Signed up {email} for {activity_name}"

    # Verify added
    resp = client.get("/activities")
    assert email in resp.json()[activity_name]["participants"]

    # Unregister
    resp = client.delete(f"/activities/{activity_name}/participants?email={email}")
    assert resp.status_code == 200
    assert resp.json()["message"] == f"Unregistered {email} from {activity_name}"

    # Verify removed
    resp = client.get("/activities")
    assert email not in resp.json()[activity_name]["participants"]


def test_signup_duplicate_returns_400(client):
    activity_name = "Chess Club"
    # michael@mergington.edu is already registered in the sample data
    existing_email = "michael@mergington.edu"
    resp = client.post(f"/activities/{activity_name}/signup?email={existing_email}")
    assert resp.status_code == 400


def test_unregister_nonexistent_returns_404(client):
    activity_name = "Chess Club"
    missing_email = "noone@nowhere.example"
    resp = client.delete(f"/activities/{activity_name}/participants?email={missing_email}")
    assert resp.status_code == 404
