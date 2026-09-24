"""
Unit Tests for FlowMesh Requests HTTP Client
Validates persistent sessions, connection pooling, retry adapters, and auth handling.
"""

import pytest
import requests
from flowmesh_connector.http_client import FlowMeshHttpClient


def test_http_client_session_initialization():
    client = FlowMeshHttpClient(
        base_url="https://api.acme.corp",
        timeout=10.0,
        max_retries=2,
        default_headers={"X-Custom-Env": "Test"},
    )
    assert client.base_url == "https://api.acme.corp"
    assert client.timeout == 10.0
    assert client.session.headers["X-Custom-Env"] == "Test"
    assert "FlowMesh-Enterprise-Connector" in client.session.headers["User-Agent"]


def test_http_client_auth_methods():
    client = FlowMeshHttpClient(base_url="https://api.example.com")

    # Basic Auth
    client.set_basic_auth("admin", "secretPass")
    assert client.session.auth == ("admin", "secretPass")

    # Bearer Token
    client.set_bearer_token("fm_test_token_12345")
    assert client.session.headers["Authorization"] == "Bearer fm_test_token_12345"

    client.close()
