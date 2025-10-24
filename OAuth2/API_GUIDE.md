# OAuth2 보호된 API 가이드

## 개요

Access Token은 단순히 인증(Authentication)만을 위한 것이 아니라, **권한 부여(Authorization)**를 통해 다양한 보호된 리소스에 접근하는 데 사용됩니다.

### Access Token으로 할 수 있는 것

1. **사용자 정보 조회** - `/userinfo`
2. **게시물 관리** - 조회, 작성 (`/api/posts`)
3. **사용자 설정 관리** - 조회, 수정 (`/api/settings`)
4. **통계 조회** - 사용자 활동 데이터 (`/api/stats`)

모든 API는 **Scope 기반 권한 제어**를 사용하여, 토큰에 포함된 scope에 따라 접근이 제한됩니다.

---

## 구현된 API 엔드포인트

### 1. 사용자 정보 조회 (UserInfo)

```http
GET /userinfo
Authorization: Bearer {access_token}
```

**응답 예시:**
```json
{
  "sub": "user1",
  "name": "홍길동",
  "email": "user1@example.com",
  "profile_image": "https://i.pravatar.cc/100?img=1"
}
```

**필요한 Scope:** `profile`, `email`

---

### 2. 게시물 조회

```http
GET /api/posts
Authorization: Bearer {access_token}
```

**응답 예시:**
```json
{
  "user": "user1",
  "total": 2,
  "posts": [
    {
      "id": 1,
      "title": "OAuth2 학습 시작",
      "content": "오늘부터 OAuth2를 배워봅니다.",
      "created_at": "2024-10-24"
    },
    {
      "id": 2,
      "title": "PKCE 이해하기",
      "content": "PKCE는 Public Client를 위한 보안 메커니즘입니다.",
      "created_at": "2024-10-24"
    }
  ]
}
```

**필요한 Scope:** `profile`

---

### 3. 게시물 작성

```http
POST /api/posts
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "title": "새로운 게시물",
  "content": "게시물 내용입니다."
}
```

**응답 예시:**
```json
{
  "id": 3,
  "title": "새로운 게시물",
  "content": "게시물 내용입니다.",
  "created_at": "2024-10-24"
}
```

**필요한 Scope:** `profile`

---

### 4. 사용자 설정 조회

```http
GET /api/settings
Authorization: Bearer {access_token}
```

**응답 예시:**
```json
{
  "language": "ko",
  "timezone": "Asia/Seoul",
  "notifications": true
}
```

**필요한 Scope:** `profile`

---

### 5. 사용자 설정 업데이트

```http
PUT /api/settings
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "notifications": false
}
```

**응답 예시:**
```json
{
  "language": "ko",
  "timezone": "Asia/Seoul",
  "notifications": false
}
```

**필요한 Scope:** `profile`

---

### 6. 사용자 통계 조회

```http
GET /api/stats
Authorization: Bearer {access_token}
```

**응답 예시:**
```json
{
  "user": "user1",
  "total_posts": 2,
  "account_created": "2024-10-24",
  "last_login": "2024-10-24 14:30:45",
  "scopes": ["profile", "email"]
}
```

**필요한 Scope:** `profile`

---

## Scope 기반 권한 제어

### Scope란?

Scope는 Access Token이 어떤 리소스에 접근할 수 있는지 정의하는 권한입니다.

### 현재 구현된 Scope

| Scope | 설명 | 접근 가능한 API |
|-------|------|----------------|
| `profile` | 사용자 프로필 정보 | `/userinfo`, `/api/posts`, `/api/settings`, `/api/stats` |
| `email` | 이메일 정보 | `/userinfo` (email 필드) |

### Scope 검증 예시

```python
@app.route('/api/posts', methods=['GET'])
@require_token(required_scopes=['profile'])
def get_posts(token_data):
    # profile scope가 없으면 403 Forbidden 반환
    ...
```

---

## 웹 UI에서 테스트하기

### Confidential Client (백엔드 웹앱)

1. `http://{HOST_IP}:8080` 접속
2. "OAuth2로 로그인" 클릭
3. `user1` / `password1`로 로그인
4. 프로필 페이지에서 다음 기능 사용:
   - **게시물 조회**: 자동으로 표시됨
   - **게시물 작성**: "➕ 새 게시물 작성" 버튼 클릭
   - **설정 변경**: "알림 켜기/끄기" 버튼 클릭
   - **통계 조회**: 자동으로 표시됨

---

## curl로 직접 테스트하기

### 1단계: Access Token 얻기

먼저 웹 UI를 통해 OAuth2 로그인을 완료하고, 프로필 페이지에서 Access Token을 복사합니다.

또는 아래 단계를 직접 수행:

```bash
# 1. Authorization Code 받기 (브라우저에서 수행)
# http://{HOST_IP}:5000/authorize?client_id=client_backend&redirect_uri=http://{HOST_IP}:8080/callback&response_type=code&scope=profile email&state=test123

# 2. Authorization Code를 Token으로 교환
curl -X POST http://{HOST_IP}:5000/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=authorization_code" \
  -d "code={AUTHORIZATION_CODE}" \
  -d "redirect_uri=http://{HOST_IP}:8080/callback" \
  -d "client_id=client_backend" \
  -d "client_secret=secret_backend_12345"
```

### 2단계: API 호출

```bash
# Access Token 설정
TOKEN="your_access_token_here"

# 사용자 정보 조회
curl -H "Authorization: Bearer $TOKEN" \
  http://{HOST_IP}:5000/userinfo

# 게시물 조회
curl -H "Authorization: Bearer $TOKEN" \
  http://{HOST_IP}:5000/api/posts

# 게시물 작성
curl -X POST http://{HOST_IP}:5000/api/posts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "curl로 작성한 게시물", "content": "API 직접 호출 테스트"}'

# 설정 조회
curl -H "Authorization: Bearer $TOKEN" \
  http://{HOST_IP}:5000/api/settings

# 설정 업데이트
curl -X PUT http://{HOST_IP}:5000/api/settings \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"notifications": false}'

# 통계 조회
curl -H "Authorization: Bearer $TOKEN" \
  http://{HOST_IP}:5000/api/stats
```

---

## 오류 처리

### 1. Access Token이 없거나 잘못된 경우

```json
{
  "error": "invalid_token",
  "message": "Missing or invalid Authorization header"
}
```

**HTTP Status:** 401 Unauthorized

---

### 2. Scope가 부족한 경우

```json
{
  "error": "insufficient_scope",
  "message": "Required scopes: ['profile']"
}
```

**HTTP Status:** 403 Forbidden

---

### 3. Token이 만료된 경우

```json
{
  "error": "invalid_token",
  "message": "Access token expired"
}
```

**HTTP Status:** 401 Unauthorized

**해결:** Refresh Token으로 새 Access Token 발급

---

## Refresh Token으로 Access Token 갱신

```bash
curl -X POST http://{HOST_IP}:5000/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=refresh_token" \
  -d "refresh_token={REFRESH_TOKEN}" \
  -d "client_id=client_backend" \
  -d "client_secret=secret_backend_12345"
```

**응답:**
```json
{
  "access_token": "new_access_token",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "new_refresh_token",
  "scope": "profile email"
}
```

---

## 핵심 포인트

### OAuth2는 인증(Authentication)과 권한 부여(Authorization)를 모두 제공

1. **인증(Authentication)**: "사용자가 누구인가?" → `/userinfo`로 확인
2. **권한 부여(Authorization)**: "사용자가 무엇을 할 수 있는가?" → Scope로 제어

### Access Token의 역할

- ✅ 사용자 신원 확인
- ✅ API 접근 권한 부여
- ✅ Scope 기반 세밀한 권한 제어
- ✅ 만료 시간을 통한 보안 관리

### 실제 서비스 예시

- **Google OAuth2**: Gmail, Drive, Calendar 등 다양한 API 접근
- **GitHub OAuth2**: Repositories, Issues, Organizations 관리
- **Facebook OAuth2**: 게시물, 친구 목록, 프로필 정보 접근

---

## 추가 학습 자료

- [OAuth2.0 RFC 6749](https://tools.ietf.org/html/rfc6749)
- [JWT (JSON Web Token)](https://jwt.io/)
- [PKCE RFC 7636](https://tools.ietf.org/html/rfc7636)

