# OAuth2 Authorization Server + Resource Server

Google, Facebook과 같은 인증 제공자 역할을 하는 서버입니다.

## 📋 기능

### Authorization Server
- ✅ `/authorize` - 사용자 로그인 및 권한 동의
- ✅ `/token` - Authorization Code → Access Token 교환
- ✅ PKCE (Proof Key for Code Exchange) 지원
- ✅ Confidential Client / Public Client 모두 지원

### Resource Server
- ✅ `/userinfo` - 사용자 정보 API
- ✅ Access Token 검증
- ✅ Scope 기반 정보 필터링

## 🚀 실행 방법

### 1. 가상환경 생성 및 활성화
```bash
cd auth-server
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 2. 의존성 설치
```bash
pip install -r requirements.txt
```

### 3. 서버 실행
```bash
python app.py
```

서버가 http://localhost:5000 에서 실행됩니다.

## 🧪 테스트 데이터

### 등록된 사용자
| 아이디 | 비밀번호 | 이름 | 이메일 |
|--------|---------|------|--------|
| user1  | pass1   | 홍길동 | user1@example.com |
| user2  | pass2   | 김철수 | user2@example.com |

### 등록된 클라이언트
| Client ID | Type | Secret | Redirect URI |
|-----------|------|--------|--------------|
| client_backend | Confidential | secret_backend | http://localhost:8080/callback |
| client_spa | Public | (없음) | http://localhost:8081/callback.html |

## 🔐 OAuth2 플로우

### Confidential Client Flow
```
1. Client → /authorize (client_id, redirect_uri, scope)
2. 사용자 로그인 및 동의
3. Authorization Server → Client (authorization code)
4. Client → /token (code, client_id, client_secret)
5. Authorization Server → Client (access_token)
6. Client → /userinfo (Bearer access_token)
7. Resource Server → Client (user data)
```

### Public Client Flow (PKCE)
```
1. Client: code_verifier 생성 (랜덤 문자열)
2. Client: code_challenge = SHA256(code_verifier)
3. Client → /authorize (client_id, redirect_uri, scope, code_challenge)
4. 사용자 로그인 및 동의
5. Authorization Server → Client (authorization code)
6. Client → /token (code, client_id, code_verifier) ※ secret 없음!
7. Authorization Server: SHA256(code_verifier) == code_challenge 검증
8. Authorization Server → Client (access_token)
9. Client → /userinfo (Bearer access_token)
10. Resource Server → Client (user data)
```

## 📡 API 엔드포인트

### GET /authorize
Authorization 요청 (로그인 화면으로 리다이렉트)

**파라미터:**
- `client_id` (필수): 클라이언트 ID
- `redirect_uri` (필수): 콜백 URI
- `response_type` (필수): `code`
- `scope` (선택): 요청 권한 (예: `profile email`)
- `state` (권장): CSRF 방지용 랜덤 문자열
- `code_challenge` (PKCE): SHA256(code_verifier)
- `code_challenge_method` (PKCE): `S256` 또는 `plain`

**예시:**
```
GET /authorize?client_id=client_backend&redirect_uri=http://localhost:8080/callback&response_type=code&scope=profile+email&state=xyz
```

### POST /token
Access Token 발급

**파라미터 (application/x-www-form-urlencoded):**
- `grant_type` (필수): `authorization_code`
- `code` (필수): Authorization Code
- `redirect_uri` (필수): Authorization 요청 시와 동일한 URI
- `client_id` (필수): 클라이언트 ID
- `client_secret` (Confidential Client 필수): 클라이언트 시크릿
- `code_verifier` (PKCE 필수): Code Verifier

**응답:**
```json
{
  "access_token": "...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "...",
  "scope": "profile email"
}
```

### GET /userinfo
사용자 정보 조회 (Resource Server)

**헤더:**
```
Authorization: Bearer {access_token}
```

**응답:**
```json
{
  "sub": "user1",
  "name": "홍길동",
  "email": "user1@example.com",
  "profile_image": "https://..."
}
```

## 🔍 로깅

서버는 다음과 같은 주요 이벤트를 로깅합니다:

```
✅ Authorization Code 발급:
   User: user1
   Client: client_backend
   Code: abcd1234...
   PKCE: True
   
✅ PKCE 검증 성공!
   Code Verifier: xyz789...
   Code Challenge: abc123...
   
✅ Access Token 발급:
   User: user1
   Client: client_backend
   Token: token123...
```

## 🛡️ 보안 고려사항

이 구현은 **학습용**입니다. 실제 운영 환경에서는:

1. ✅ HTTPS 필수
2. ✅ Authorization Code는 일회용 (이미 구현됨)
3. ✅ Redirect URI 엄격히 검증 (이미 구현됨)
4. ✅ State 파라미터로 CSRF 방지 (클라이언트에서 구현)
5. ⚠️ 데이터베이스 사용 (현재는 인메모리)
6. ⚠️ 토큰을 DB/Redis에 저장
7. ⚠️ Rate Limiting 구현
8. ⚠️ 비밀번호 해싱 (bcrypt, argon2)
9. ⚠️ CORS 정책 엄격히 설정

## 🧪 테스트 방법

### 1. 서버 상태 확인
```bash
curl http://localhost:5000/
```

### 2. Authorization 플로우 수동 테스트
```bash
# 브라우저에서 열기
http://localhost:5000/authorize?client_id=client_backend&redirect_uri=http://localhost:8080/callback&response_type=code&scope=profile%20email
```

### 3. Token 발급 테스트
```bash
curl -X POST http://localhost:5000/token \
  -d "grant_type=authorization_code" \
  -d "code=YOUR_AUTHORIZATION_CODE" \
  -d "redirect_uri=http://localhost:8080/callback" \
  -d "client_id=client_backend" \
  -d "client_secret=secret_backend"
```

### 4. UserInfo 조회 테스트
```bash
curl http://localhost:5000/userinfo \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 📚 참고 자료

- [RFC 6749 - OAuth 2.0 Framework](https://datatracker.ietf.org/doc/html/rfc6749)
- [RFC 7636 - PKCE](https://datatracker.ietf.org/doc/html/rfc7636)
- [RFC 7662 - Token Introspection](https://datatracker.ietf.org/doc/html/rfc7662)

## 🐛 문제 해결

### 포트가 이미 사용 중
```bash
lsof -i :5000
kill -9 <PID>
```

### 모듈을 찾을 수 없음
```bash
pip install -r requirements.txt
```

### CORS 오류
개발 중에는 이미 모든 Origin을 허용하도록 설정되어 있습니다.

