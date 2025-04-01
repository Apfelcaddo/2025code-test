#3. Production-Grade API Decorators
# Task:
# ■ Create a decorator enforcing JWT validation and Datadog
# logging.
# ■ Unit tests for valid/invalid tokens and logging toggles.
# Deliverables:
# ■ Decorator code + pytest scripts

# decorators.py
import jwt #PyJWT library for handling JWT
import os # For reading environment variables or other configurations
from functools import wraps # For creating decorators
from datadog import initialize, statsd # For logging with datadog
import requests # For making HTTP requests
from flask import request, jsonify # For handling HTTP requests and responses

# Initialize DataDog with configuration settings 
DATADOG_OPTIONS = {
    'api_key': "03cd586f542dae21f0c423d4e49937a0",
    'app_key': "03cd586f542dae21f0c423d4e49937a0",
}

# Use the same secret key as in tests
JWT_SECRET = os.environ.get('JWT_SECRET', 'test_secret')
initialize(**DATADOG_OPTIONS)

def jwt_and_datadog_logger(function):
    '''Fetch JWT from the HTTP request header, validates it, and logs it with Datadog
    '''
    @wraps(function)
    def wrapper(*args, **kwargs):
        # step1: obtain the 'Authorization' header from the Flask request object
        auth_header = request.headers.get('Authorization', None)
        if not auth_header:
            # return a 401 response if there is no Authorization header
            return jsonify({'message': 'Token is missing'}), 401

        # step2: verify that the header starts with "Bearer" and extract the actual token
        if not auth_header.startswith("Bearer"):
            # if the format is incorrect, respond with 401
            return jsonify({"message":"Invalid Authorization header format"}), 401

        token = auth_header.split(" ")[1]

        # step3: validate the JWT token: if the token is expired or invalid, exceptions are raised and should be handled accordingly
        try:
            # decode and validate the token using JWT_SECRET
            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            
            # log an event to Datadog after successful validation
            statsd.event(
                title="JWT Access",
                text="A valid JWT token was provided",
                alert_type="info"
            )
            # proceed to call the original decorated function if the token is valid
            return function(*args, **kwargs)
            
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except (jwt.InvalidTokenError, TypeError):
            return jsonify({'message': 'Invalid token'}), 401

    return wrapper
