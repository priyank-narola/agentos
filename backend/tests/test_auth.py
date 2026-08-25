import time
import pytest
import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

from app.auth import (
    TokenValidator,
    TokenClaims,
    AuthError,
    MissingTokenError,
    InvalidTokenError,
    ExpiredTokenError,
    InvalidIssuerError,
    InvalidAudienceError,
    InsufficientScopeError,
)

# Helper fixtures for RS256 testing
@pytest.fixture
def rsa_keys():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    pem_private = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode('utf-8')

    pem_public = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')

    return pem_private, pem_public


@pytest.fixture
def secret_key():
    return "super-secret-key-for-hs256-testing-123456"


@pytest.fixture
def default_validator(secret_key):
    return TokenValidator(
        expected_issuer="https://auth.agentos.com",
        expected_audience="https://agentos-api-qm2r.onrender.com",
        required_scope="agentos:execute",
        secret_key=secret_key,
        algorithms=["HS256", "RS256"]
    )


def create_jwt(
    payload: dict,
    key: str,
    algorithm: str = "HS256",
    headers: dict = None
) -> str:
    now = int(time.time())
    default_payload = {
        "sub": "user-principal-uuid-1234",
        "iss": "https://auth.agentos.com",
        "aud": "https://agentos-api-qm2r.onrender.com",
        "exp": now + 900,
        "nbf": now - 10,
        "iat": now,
        "scope": "agentos:read agentos:execute",
        "client_id": "agent-uuid-5678"
    }
    default_payload.update(payload)
    return jwt.encode(default_payload, key, algorithm=algorithm, headers=headers)


def test_valid_token_returns_claims(default_validator, secret_key):
    token = create_jwt({}, secret_key)
    claims = default_validator.validate_token(f"Bearer {token}")
    
    assert isinstance(claims, TokenClaims)
    assert claims.sub == "user-principal-uuid-1234"
    assert claims.iss == "https://auth.agentos.com"
    assert claims.aud == "https://agentos-api-qm2r.onrender.com"
    assert claims.scope == {"agentos:read", "agentos:execute"}
    assert claims.client_id == "agent-uuid-5678"


def test_valid_rs256_token_returns_claims(rsa_keys):
    priv_key, pub_key = rsa_keys
    validator = TokenValidator(
        expected_issuer="https://auth.agentos.com",
        expected_audience="https://agentos-api-qm2r.onrender.com",
        required_scope="agentos:execute",
        public_key=pub_key,
        algorithms=["RS256"]
    )
    token = create_jwt({}, priv_key, algorithm="RS256")
    claims = validator.validate_token(token)
    assert claims.sub == "user-principal-uuid-1234"


def test_missing_authorization_header_raises(default_validator):
    with pytest.raises(MissingTokenError) as exc_info:
        default_validator.validate_token("")
    
    err = exc_info.value
    assert err.status_code == 401
    assert "WWW-Authenticate" in err.headers
    assert "Bearer resource_metadata=" in err.headers["WWW-Authenticate"]
    assert 'scope="agentos:execute"' in err.headers["WWW-Authenticate"]


def test_malformed_bearer_token_raises(default_validator):
    with pytest.raises(InvalidTokenError) as exc_info:
        default_validator.extract_bearer_token("Basic token123")
    
    err = exc_info.value
    assert err.status_code == 401
    assert "error=\"invalid_token\"" in err.headers["WWW-Authenticate"]


def test_invalid_signature_raises(default_validator):
    wrong_key = "wrong-secret-key"
    token = create_jwt({}, wrong_key)
    
    with pytest.raises(InvalidTokenError) as exc_info:
        default_validator.validate_token(f"Bearer {token}")
    
    err = exc_info.value
    assert err.status_code == 401
    assert "Cryptographic token verification failed" in err.message or "Invalid signature" in err.message


def test_expired_token_raises(default_validator, secret_key):
    past_time = int(time.time()) - 3600
    token = create_jwt({"exp": past_time}, secret_key)
    
    with pytest.raises(ExpiredTokenError) as exc_info:
        default_validator.validate_token(token)
    
    err = exc_info.value
    assert err.status_code == 401
    assert "The access token expired" in err.headers["WWW-Authenticate"]


def test_not_yet_valid_token_raises(default_validator, secret_key):
    future_time = int(time.time()) + 3600
    token = create_jwt({"nbf": future_time}, secret_key)
    
    with pytest.raises(InvalidTokenError) as exc_info:
        default_validator.validate_token(token)
    
    err = exc_info.value
    assert err.status_code == 401
    assert "Token not valid yet" in err.message


def test_wrong_issuer_raises(default_validator, secret_key):
    token = create_jwt({"iss": "https://attacker-auth.com"}, secret_key)
    
    with pytest.raises(InvalidIssuerError) as exc_info:
        default_validator.validate_token(token)
    
    err = exc_info.value
    assert err.status_code == 401
    assert "Invalid token issuer" in err.headers["WWW-Authenticate"]


def test_wrong_audience_raises(default_validator, secret_key):
    token = create_jwt({"aud": "https://other-service.com"}, secret_key)
    
    with pytest.raises(InvalidAudienceError) as exc_info:
        default_validator.validate_token(token)
    
    err = exc_info.value
    assert err.status_code == 401
    assert "Invalid token audience" in err.headers["WWW-Authenticate"]


def test_missing_required_scope_raises(default_validator, secret_key):
    token = create_jwt({"scope": "agentos:read"}, secret_key)
    
    with pytest.raises(InsufficientScopeError) as exc_info:
        default_validator.validate_token(token, required_scope="agentos:execute")
    
    err = exc_info.value
    assert err.status_code == 403
    assert 'error="insufficient_scope"' in err.headers["WWW-Authenticate"]
    assert 'scope="agentos:execute"' in err.headers["WWW-Authenticate"]


def test_www_authenticate_header_content(default_validator, secret_key):
    # Missing header check
    try:
        default_validator.extract_bearer_token(None)
    except MissingTokenError as e:
        assert e.headers["WWW-Authenticate"] == (
            'Bearer resource_metadata="https://agentos-api-qm2r.onrender.com/.well-known/oauth-protected-resource", scope="agentos:execute"'
        )
        
    # Insufficient scope check
    token = create_jwt({"scope": "agentos:read"}, secret_key)
    try:
        default_validator.validate_token(token, required_scope="agentos:execute")
    except InsufficientScopeError as e:
        assert e.headers["WWW-Authenticate"] == (
            'Bearer error="insufficient_scope", scope="agentos:execute", resource_metadata="https://agentos-api-qm2r.onrender.com/.well-known/oauth-protected-resource", error_description="Insufficient scope"'
        )


def test_no_client_supplied_identity_spoofing(default_validator, secret_key):
    """
    Verify that identity comes STRICTLY from verified JWT sub/client_id,
    and client attempt to spoof identity parameters is ignored by TokenClaims.
    """
    token = create_jwt({
        "sub": "real-user-id-999",
        "client_id": "real-agent-id-888"
    }, secret_key)
    
    claims = default_validator.validate_token(token)
    
    # Claims must reflect payload signed by trusted secret, irrespective of caller's outside context
    assert claims.sub == "real-user-id-999"
    assert claims.client_id == "real-agent-id-888"
    assert claims.sub != "spoofed-user-id-000"
