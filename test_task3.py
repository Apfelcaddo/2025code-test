import pytest
from unittest.mock import patch, Mock
import jwt
import time
from flask import Flask
from task3 import jwt_and_datadog_logger

# Test configuration
TEST_SECRET = 'test_secret'
VALID_PAYLOAD = {'user_id': 123, 'exp': int(time.time()) + 3600}
EXPIRED_PAYLOAD = {'user_id': 123, 'exp': int(time.time()) - 3600}

@pytest.fixture
def app():
    app = Flask(__name__)
    
    # Create test endpoint with our decorator
    @app.route('/test')
    @jwt_and_datadog_logger
    def test_endpoint():
        return {'message': 'success'}, 200
    
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def create_token(payload):
        # Use the same TEST_SECRET for both encoding and decoding
    return f"Bearer {jwt.encode(payload, TEST_SECRET, algorithm='HS256')}"

@pytest.fixture(autouse=True)
def setup_environment(monkeypatch):
    # Ensure JWT_SECRET is set for all tests
    monkeypatch.setenv('JWT_SECRET', TEST_SECRET)

class TestJWTAndDatadogDecorator:
    
    @patch('task3.statsd')
    def test_valid_token(self, mock_statsd, client):
        """Test endpoint with valid token"""
        headers = {'Authorization': create_token(VALID_PAYLOAD)}
        response = client.get('/test', headers=headers)
        assert response.status_code == 200
        mock_statsd.event.assert_called_once()

    def test_missing_token(self, client):
        """Test endpoint with no token"""
        response = client.get('/test')
        assert response.status_code == 401
        assert b'Token is missing' in response.data

    def test_invalid_token_format(self, client):
        """Test endpoint with malformed token"""
        headers = {'Authorization': 'InvalidFormat token'}
        response = client.get('/test', headers=headers)
        assert response.status_code == 401

    def test_expired_token(self, client):
        """Test endpoint with expired token"""
        headers = {'Authorization': create_token(EXPIRED_PAYLOAD)}
        response = client.get('/test', headers=headers)
        assert response.status_code == 401
        assert b'Token has expired' in response.data

    @patch('task3.statsd')
    def test_logging_called(self, mock_statsd, client):
        """Test that Datadog logging is called"""
        headers = {'Authorization': create_token(VALID_PAYLOAD)}
        client.get('/test', headers=headers)
        mock_statsd.event.assert_called_with(
            title="JWT Access",
            text="A valid JWT token was provided",
            alert_type="info"
        )
