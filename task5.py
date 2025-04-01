# 5. Robust Database Connections
# Task:
# ■ Build a context manager for AWS Aurora with retries and
# OpenTelemetry tracing.
# ■ Simulate connection failures and validate retry logic.
# Deliverables:
# ■ Context manager code.
# ■ Failure recovery test logs.

import time  # for delays in retries
import random  # for simulate random connection failures
import mysql.connector  # for connecting to the database
from opentelemetry import trace  # for OpenTelemetry tracing
from opentelemetry.trace import Span  # for creating and managing tracing Spans
from opentelemetry.sdk.trace import TracerProvider  # Tracer provider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor  # for exporting spans


class AuroraDBConnection:
    def __init__(self, host, port, user, password, db_name):
        # store the parameters needed for DB connection
        self.host = host  # the database host address
        self.port = port  # the database port
        self.user = user  # the database username
        self.password = password  # the database password
        self.db_name = db_name  # the name of the database to connect to

        # other settings
        self.max_retries = 5
        self.backoff_factor = 2
        self.retry_delay = 2

        self.tracer = None  # set up tracer

        self.connection = None  # initialize the database connection object

        # Initialize OpenTelemetry
        trace.set_tracer_provider(TracerProvider())
        self.tracer = trace.get_tracer(__name__)

    def __enter__(self):
        """automatically called when the context manager is entered"""
        self.connect()
        return self.connection

    def __exit__(self, exc_type, exc_value, traceback):
        """automatically called when the context manager is exited"""
        self.close()

    def connect(self):
        """attempt to connect to the database with retry logic"""
        with self.tracer.start_as_current_span("db_connect") as span:
            for attempt in range(self.max_retries):
                try:
                    # Simulate random failures for testing
                    if random.random() < 0.3:  # 30% chance of failure
                        raise mysql.connector.Error("Simulated connection failure")
                    
                    span.set_attribute("connection.attempt", attempt + 1)
                    self.connection = mysql.connector.connect(
                        host=self.host,
                        port=self.port,
                        user=self.user,
                        password=self.password,
                        database=self.db_name
                    )
                    print("Connected to the database")
                    span.set_attribute("connection.success", True)
                    return
                except mysql.connector.Error as err:
                    print(f"Connection attempt {attempt + 1} failed: {err}")
                    span.set_attribute("connection.error", str(err))
                    if attempt < self.max_retries - 1:
                        wait_time = self.retry_delay * (self.backoff_factor ** attempt)
                        span.add_event("retrying", {"wait_time": wait_time})
                        time.sleep(wait_time)
                    else:
                        span.set_attribute("connection.success", False)
                        span.set_status(trace.Status(trace.StatusCode.ERROR))
                        raise

    def close(self):
        """Close the database connection"""
        with self.tracer.start_as_current_span("db_close") as span:
            if self.connection:
                try:
                    self.connection.close()
                    span.set_attribute("connection.closed", True)
                    print("Connection closed.")
                except Exception as e:
                    span.set_attribute("connection.error", str(e))
                    span.set_status(trace.Status(trace.StatusCode.ERROR))
                    raise

# Example usage and test
if __name__ == "__main__":
    db_config = {
        "host": "localhost",
        "port": 3306,
        "user": "test_user",
        "password": "test_password",
        "db_name": "test_db"
    }
    
    try:
        print("Attempting to connect to the database...")
        with AuroraDBConnection(**db_config) as conn:
            print("Successfully connected to database")
            # Perform database operations here
    except mysql.connector.Error as e:
        print(f"Database operation failed: {e}")
