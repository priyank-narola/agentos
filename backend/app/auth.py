import time
from dataclasses import dataclass, field
from typing import Any, Optional, Union
import jwt
from jwt import PyJWKClient

from app.config import settings


@dataclass
class TokenClaims:
    """Validated OAuth 2.1 token claims."""
    sub: str
    iss: str
    aud: Union[str, list[str]]
    scope: set[str]
    exp: Optional[int] = None
    nbf: Optional[int] = None
    iat: Optional[int] = None
    client_id: Optional[str] = None
    azp: Optional[str] = None
    raw_payload: dict[str, Any] = field(default_factory=dict)


class AuthError(Exception):
    """Base exception for MCP authentication errors."""
    def __init__(self, message: str, status_code: int = 401, headers: Optional[dict[str, str]] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.headers = headers or {}


class MissingTokenError(AuthError):
    """Raised when Authorization header is missing or empty."""
    def __init__(
        self,
        message: str = "Missing Authorization header",
        resource_metadata: str = "",
        scope: str = ""
    ):
        header_val = f'Bearer resource_metadata="{resource_metadata}"'
        if scope:
            header_val += f', scope="{scope}"'
        headers = {"WWW-Authenticate": header_val}
        super().__init__(message, status_code=401, headers=headers)


class InvalidTokenError(AuthError):
    """Raised when token validation fails (signature, malformed, invalid claims)."""
    def __init__(
        self,
        message: str = "Invalid Bearer token",
        resource_metadata: str = "",
        scope: str = "",
        error_description: Optional[str] = None
    ):
        header_parts = [
            f'resource_metadata="{resource_metadata}"',
            f'error="invalid_token"'
        ]
        if scope:
            header_parts.append(f'scope="{scope}"')
        if error_description:
            header_parts.append(f'error_description="{error_description}"')
        headers = {"WWW-Authenticate": "Bearer " + ", ".join(header_parts)}
        super().__init__(message, status_code=401, headers=headers)


class ExpiredTokenError(InvalidTokenError):
    """Raised when token is past expiration (exp)."""
    def __init__(
        self,
        message: str = "Token has expired",
        resource_metadata: str = "",
        scope: str = ""
    ):
        super().__init__(
            message=message,
            resource_metadata=resource_metadata,
            scope=scope,
            error_description="The access token expired"
        )


class InvalidIssuerError(InvalidTokenError):
    """Raised when token issuer (iss) does not match expected issuer."""
    def __init__(
        self,
        message: str = "Invalid token issuer",
        resource_metadata: str = "",
        scope: str = ""
    ):
        super().__init__(
            message=message,
            resource_metadata=resource_metadata,
            scope=scope,
            error_description="Invalid token issuer"
        )


class InvalidAudienceError(InvalidTokenError):
    """Raised when token audience (aud) does not match expected audience/resource."""
    def __init__(
        self,
        message: str = "Invalid token audience",
        resource_metadata: str = "",
        scope: str = ""
    ):
        super().__init__(
            message=message,
            resource_metadata=resource_metadata,
            scope=scope,
            error_description="Invalid token audience"
        )


class InsufficientScopeError(AuthError):
    """Raised when token lacks required OAuth scope (HTTP 403)."""
    def __init__(
        self,
        message: str = "Insufficient scope for requested operation",
        resource_metadata: str = "",
        scope: str = ""
    ):
        header_parts = [
            'error="insufficient_scope"',
            f'scope="{scope}"',
            f'resource_metadata="{resource_metadata}"',
            'error_description="Insufficient scope"'
        ]
        headers = {"WWW-Authenticate": "Bearer " + ", ".join(header_parts)}
        super().__init__(message, status_code=403, headers=headers)


class TokenValidator:
    """
    Transport-independent OAuth 2.1 Bearer Token Validator for AgentOS MCP Server.
    Validates signature, issuer, audience/resource, expiration, not-before, and scopes.
    Identity is extracted STRICTLY from cryptographically verified claims (no header spoofing).
    """

    def __init__(
        self,
        expected_issuer: Optional[str] = None,
        expected_audience: Optional[str] = None,
        required_scope: Optional[str] = None,
        jwks_url: Optional[str] = None,
        public_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        algorithms: Optional[list[str]] = None,
        resource_metadata_url: Optional[str] = None
    ):
        self.expected_issuer = expected_issuer or settings.mcp_auth_issuer
        self.expected_audience = expected_audience or settings.mcp_auth_audience
        self.required_scope = required_scope or settings.mcp_auth_required_scope
        self.jwks_url = jwks_url or settings.mcp_auth_jwks_url
        self.public_key = public_key or settings.mcp_auth_public_key
        self.secret_key = secret_key or settings.mcp_auth_secret_key
        self.algorithms = algorithms or ["RS256", "ES256", "HS256"]
        
        # Canonical Protected Resource Metadata URL for WWW-Authenticate headers
        self.resource_metadata_url = (
            resource_metadata_url or 
            f"{self.expected_audience.rstrip('/')}/.well-known/oauth-protected-resource"
        )

        self._jwks_client: Optional[PyJWKClient] = None
        if self.jwks_url and not self.public_key and not self.secret_key:
            try:
                self._jwks_client = PyJWKClient(self.jwks_url)
            except Exception:
                self._jwks_client = None

    def extract_bearer_token(self, auth_header: Optional[str]) -> str:
        """Extract token string from Authorization header value."""
        if not auth_header or not auth_header.strip():
            raise MissingTokenError(
                message="Missing Authorization header",
                resource_metadata=self.resource_metadata_url,
                scope=self.required_scope
            )
        
        parts = auth_header.strip().split(maxsplit=1)
        if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1]:
            raise InvalidTokenError(
                message="Malformed Authorization header format. Expected 'Bearer <token>'",
                resource_metadata=self.resource_metadata_url,
                scope=self.required_scope,
                error_description="Malformed Authorization header"
            )
        
        return parts[1]

    def _get_signing_key(self, unverified_header: dict[str, Any], token: str) -> Any:
        """Determine signing key for JWT verification."""
        if self.secret_key:
            return self.secret_key
        if self.public_key:
            return self.public_key
        if self._jwks_client:
            try:
                signing_key = self._jwks_client.get_signing_key_from_jwt(token)
                return signing_key.key
            except Exception as e:
                raise InvalidTokenError(
                    message=f"Unable to retrieve signing key from JWKS: {str(e)}",
                    resource_metadata=self.resource_metadata_url,
                    scope=self.required_scope,
                    error_description="Signing key not found"
                )
        
        raise InvalidTokenError(
            message="No verification key configured on server",
            resource_metadata=self.resource_metadata_url,
            scope=self.required_scope,
            error_description="Server configuration error"
        )

    def validate_token(
        self,
        token_or_header: str,
        required_scope: Optional[str] = None
    ) -> TokenClaims:
        """
        Validate Bearer token and return verified TokenClaims.
        
        :param token_or_header: Raw token string or full 'Bearer <token>' header.
        :param required_scope: Override required scope for this operation.
        """
        target_scope = required_scope if required_scope is not None else self.required_scope
        
        # 1. Extract Bearer token if header passed
        if token_or_header.strip().lower().startswith("bearer ") or " " in token_or_header.strip():
            token = self.extract_bearer_token(token_or_header)
        else:
            token = token_or_header.strip()
            if not token:
                raise MissingTokenError(
                    message="Missing token",
                    resource_metadata=self.resource_metadata_url,
                    scope=target_scope
                )

        # 2. Decode unverified header to get algorithm
        try:
            unverified_header = jwt.get_unverified_header(token)
        except Exception as e:
            raise InvalidTokenError(
                message=f"Invalid JWT header: {str(e)}",
                resource_metadata=self.resource_metadata_url,
                scope=target_scope,
                error_description="Invalid JWT structure"
            )

        alg = unverified_header.get("alg")
        if not alg or alg not in self.algorithms:
            raise InvalidTokenError(
                message=f"Unsupported algorithm '{alg}'",
                resource_metadata=self.resource_metadata_url,
                scope=target_scope,
                error_description="Unsupported token algorithm"
            )

        # 3. Retrieve key and verify signature & claims
        key = self._get_signing_key(unverified_header, token)

        try:
            payload = jwt.decode(
                token,
                key=key,
                algorithms=[alg],
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_nbf": True,
                    "verify_iat": True,
                    "verify_aud": False,  # Custom strict aud check below for clear errors
                    "verify_iss": False,  # Custom strict iss check below for clear errors
                    "require": ["sub", "iss", "aud", "exp"]
                }
            )
        except jwt.ExpiredSignatureError:
            raise ExpiredTokenError(
                message="Token has expired",
                resource_metadata=self.resource_metadata_url,
                scope=target_scope
            )
        except jwt.ImmatureSignatureError:
            raise InvalidTokenError(
                message="Token not valid yet (nbf claim in future)",
                resource_metadata=self.resource_metadata_url,
                scope=target_scope,
                error_description="Token not valid yet"
            )
        except jwt.MissingRequiredClaimError as e:
            raise InvalidTokenError(
                message=f"Missing required claim: {e.claim}",
                resource_metadata=self.resource_metadata_url,
                scope=target_scope,
                error_description=f"Missing claim: {e.claim}"
            )
        except jwt.PyJWTError as e:
            raise InvalidTokenError(
                message=f"Cryptographic token verification failed: {str(e)}",
                resource_metadata=self.resource_metadata_url,
                scope=target_scope,
                error_description="Invalid signature or token structure"
            )

        # 4. Strict Issuer Validation (iss)
        token_iss = payload.get("iss")
        if token_iss != self.expected_issuer:
            raise InvalidIssuerError(
                message=f"Token issuer '{token_iss}' does not match expected '{self.expected_issuer}'",
                resource_metadata=self.resource_metadata_url,
                scope=target_scope
            )

        # 5. Strict Audience / Resource Validation (aud)
        token_aud = payload.get("aud")
        aud_valid = False
        if isinstance(token_aud, str):
            aud_valid = (token_aud == self.expected_audience)
        elif isinstance(token_aud, list):
            aud_valid = (self.expected_audience in token_aud)

        if not aud_valid:
            raise InvalidAudienceError(
                message=f"Token audience '{token_aud}' does not contain expected resource '{self.expected_audience}'",
                resource_metadata=self.resource_metadata_url,
                scope=target_scope
            )

        # 6. Subject (sub) validation
        sub = payload.get("sub")
        if not sub or not isinstance(sub, str) or not sub.strip():
            raise InvalidTokenError(
                message="Token subject (sub) claim must be a non-empty string",
                resource_metadata=self.resource_metadata_url,
                scope=target_scope,
                error_description="Invalid sub claim"
            )

        # 7. Scope Validation (scope / scp)
        token_scopes: set[str] = set()
        raw_scope = payload.get("scope") or payload.get("scp")
        if isinstance(raw_scope, str):
            token_scopes = set(raw_scope.strip().split())
        elif isinstance(raw_scope, list):
            token_scopes = set(str(s) for s in raw_scope)

        if target_scope:
            required_scopes_set = set(target_scope.strip().split())
            if not required_scopes_set.issubset(token_scopes):
                raise InsufficientScopeError(
                    message=f"Token scopes '{' '.join(token_scopes)}' missing required scope '{target_scope}'",
                    resource_metadata=self.resource_metadata_url,
                    scope=target_scope
                )

        # 8. Extract client_id and azp for agent identity mapping
        client_id_claim = payload.get("client_id") or payload.get("cid")
        azp_claim = payload.get("azp")
        
        client_id = str(client_id_claim) if client_id_claim else (str(azp_claim) if azp_claim else None)
        azp = str(azp_claim) if azp_claim else None

        return TokenClaims(
            sub=sub.strip(),
            iss=token_iss,
            aud=token_aud,
            scope=token_scopes,
            exp=payload.get("exp"),
            nbf=payload.get("nbf"),
            iat=payload.get("iat"),
            client_id=client_id,
            azp=azp,
            raw_payload=payload
        )
