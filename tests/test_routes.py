import pytest
import os
from app import create_app


@pytest.fixture
def client():
    os.environ['SUPABASE_URL'] = 'https://dummy.supabase.co'
    os.environ['SUPABASE_KEY'] = 'dummy_key'
    os.environ['FLASK_SECRET_KEY'] = 'test-secret'
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_index_route(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b"Budget Buddy" in response.data


def test_login_route(client):
    response = client.get('/login')
    assert response.status_code == 200
    assert b"Sign in" in response.data


def test_register_route(client):
    response = client.get('/register')
    assert response.status_code == 200
    assert b"Create Account" in response.data


def test_protected_routes_redirect_without_auth(client):
    routes = [
        '/dashboard',
        '/transactions',
        '/budget',
        '/reports',
        '/goals',
        '/receipt',
        '/coach',
        '/simulator',
    ]
    for route in routes:
        response = client.get(route)
        assert response.status_code == 302, f"Route {route} should redirect when not logged in"
