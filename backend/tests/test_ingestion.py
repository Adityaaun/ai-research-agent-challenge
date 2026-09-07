import pytest
import asyncio
from httpx import Request
from backend.app.ingestion.parser import is_safe_url, verify_request

def test_is_safe_url():
    # Valid URLs
    assert is_safe_url("https://en.wikipedia.org/wiki/Harry_Potter") == True
    assert is_safe_url("http://example.com/path?q=1") == True
    
    # Invalid schemes
    assert is_safe_url("ftp://example.com") == False
    assert is_safe_url("file:///etc/passwd") == False
    
    # Localhost/Loopback
    assert is_safe_url("http://localhost:8000") == False
    assert is_safe_url("http://127.0.0.1") == False
    assert is_safe_url("http://0.0.0.0") == False
    
    # Internal IP ranges (Private)
    assert is_safe_url("http://10.0.0.5") == False
    assert is_safe_url("http://192.168.1.100") == False
    assert is_safe_url("http://172.16.0.1") == False
    
    # Link local
    assert is_safe_url("http://169.254.169.254") == False

@pytest.mark.asyncio
async def test_verify_request_hook():
    valid_req = Request("GET", "https://google.com")
    # Should not raise
    await verify_request(valid_req)
    
    invalid_req = Request("GET", "http://127.0.0.1/admin")
    with pytest.raises(ValueError, match="URL points to a private or internal network address."):
        await verify_request(invalid_req)
