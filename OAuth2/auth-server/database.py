"""
간단한 인메모리 데이터베이스
실제 운영에서는 PostgreSQL, MySQL 등을 사용
"""
import secrets
from datetime import datetime, timedelta

# 사용자 데이터베이스
USERS = {
    "user1": {
        "password": "pass1",
        "name": "홍길동",
        "email": "user1@example.com",
        "profile_image": "https://via.placeholder.com/150"
    },
    "user2": {
        "password": "pass2",
        "name": "김철수",
        "email": "user2@example.com",
        "profile_image": "https://via.placeholder.com/150"
    }
}

# 등록된 클라이언트 애플리케이션
CLIENTS = {
    "client_backend": {
        "client_secret": "secret_backend",
        "client_type": "confidential",  # Confidential Client
        "redirect_uris": ["http://localhost:8080/callback"],
        "name": "Backend Web App",
        "scopes": ["profile", "email"]
    },
    "client_spa": {
        "client_secret": None,  # Public Client는 secret 없음
        "client_type": "public",  # Public Client
        "redirect_uris": ["http://localhost:8081/callback.html"],
        "name": "SPA Application",
        "scopes": ["profile", "email"]
    }
}

# Authorization Code 저장소 (임시)
# 구조: {code: {client_id, user_id, redirect_uri, expires_at, code_challenge, code_challenge_method}}
authorization_codes = {}

# Access Token 저장소
# 구조: {token: {user_id, client_id, scopes, expires_at}}
access_tokens = {}

# Refresh Token 저장소
refresh_tokens = {}


def verify_user(username, password):
    """사용자 인증"""
    user = USERS.get(username)
    if user and user["password"] == password:
        return username
    return None


def get_user(username):
    """사용자 정보 조회"""
    user = USERS.get(username)
    if user:
        return {
            "username": username,
            "name": user["name"],
            "email": user["email"],
            "profile_image": user["profile_image"]
        }
    return None


def verify_client(client_id, client_secret=None):
    """클라이언트 검증"""
    client = CLIENTS.get(client_id)
    if not client:
        return False
    
    # Public Client는 secret 검증 안 함
    if client["client_type"] == "public":
        return True
    
    # Confidential Client는 secret 검증 필수
    return client.get("client_secret") == client_secret


def get_client(client_id):
    """클라이언트 정보 조회"""
    return CLIENTS.get(client_id)


def verify_redirect_uri(client_id, redirect_uri):
    """Redirect URI 검증 - 보안상 중요!"""
    client = CLIENTS.get(client_id)
    if not client:
        return False
    return redirect_uri in client["redirect_uris"]


def generate_authorization_code(client_id, user_id, redirect_uri, scopes, 
                                code_challenge=None, code_challenge_method=None):
    """Authorization Code 생성"""
    code = secrets.token_urlsafe(32)
    authorization_codes[code] = {
        "client_id": client_id,
        "user_id": user_id,
        "redirect_uri": redirect_uri,
        "scopes": scopes,
        "expires_at": datetime.now() + timedelta(minutes=10),
        "code_challenge": code_challenge,
        "code_challenge_method": code_challenge_method
    }
    return code


def verify_authorization_code(code, client_id, redirect_uri):
    """Authorization Code 검증"""
    auth_code = authorization_codes.get(code)
    
    if not auth_code:
        return None, "Invalid authorization code"
    
    # 만료 확인
    if datetime.now() > auth_code["expires_at"]:
        del authorization_codes[code]
        return None, "Authorization code expired"
    
    # Client ID 확인
    if auth_code["client_id"] != client_id:
        return None, "Client ID mismatch"
    
    # Redirect URI 확인 (보안상 중요!)
    if auth_code["redirect_uri"] != redirect_uri:
        return None, "Redirect URI mismatch"
    
    # 사용된 코드는 삭제 (일회용)
    del authorization_codes[code]
    
    return auth_code, None


def generate_access_token(user_id, client_id, scopes):
    """Access Token 생성"""
    token = secrets.token_urlsafe(32)
    access_tokens[token] = {
        "user_id": user_id,
        "client_id": client_id,
        "scopes": scopes,
        "expires_at": datetime.now() + timedelta(hours=1)
    }
    return token


def generate_refresh_token(user_id, client_id, scopes):
    """Refresh Token 생성"""
    token = secrets.token_urlsafe(32)
    refresh_tokens[token] = {
        "user_id": user_id,
        "client_id": client_id,
        "scopes": scopes,
        "expires_at": datetime.now() + timedelta(days=30)
    }
    return token


def verify_access_token(token):
    """Access Token 검증"""
    token_data = access_tokens.get(token)
    
    if not token_data:
        return None, "Invalid token"
    
    # 만료 확인
    if datetime.now() > token_data["expires_at"]:
        del access_tokens[token]
        return None, "Token expired"
    
    return token_data, None


def verify_code_challenge(code_verifier, code_challenge, method="S256"):
    """PKCE Code Challenge 검증"""
    import hashlib
    import base64
    
    if method == "S256":
        # SHA256 해싱
        verifier_hash = hashlib.sha256(code_verifier.encode()).digest()
        computed_challenge = base64.urlsafe_b64encode(verifier_hash).decode().rstrip("=")
        return computed_challenge == code_challenge
    elif method == "plain":
        # Plain text 비교
        return code_verifier == code_challenge
    
    return False

