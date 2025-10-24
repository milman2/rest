# Confidential Client - 백엔드 웹 애플리케이션

`client_secret`을 안전하게 보관할 수 있는 서버 사이드 애플리케이션입니다.

## 🎯 특징

- ✅ **Confidential Client** - `client_secret`을 백엔드에서 안전하게 사용
- ✅ **Authorization Code Flow** - 표준 OAuth2 플로우
- ✅ **Server-side Token Exchange** - 토큰 교환을 백엔드에서 처리
- ✅ **State Parameter** - CSRF 공격 방지
- ✅ **Session Management** - 사용자 세션 관리

## 📦 OAuth2 설정

```python
CLIENT_ID = "client_backend"
CLIENT_SECRET = "secret_backend"  # ⭐ 백엔드에서 안전하게 보관
REDIRECT_URI = "http://localhost:8080/callback"
AUTHORIZATION_SERVER = "http://localhost:5000"
```

## 🚀 실행 방법

### 1. Authorization Server가 실행 중인지 확인
```bash
# 다른 터미널에서
cd ../auth-server
source venv/bin/activate
python app.py
```

### 2. 가상환경 생성 및 활성화
```bash
cd client-backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

### 4. 서버 실행
```bash
python app.py
```

서버가 http://localhost:8080 에서 실행됩니다.

### 5. 브라우저에서 테스트
```
http://localhost:8080
```

## 🔄 OAuth2 플로우

```
1. 사용자가 "로그인" 버튼 클릭
   ↓
2. Client Backend가 사용자를 Authorization Server로 리다이렉트
   GET /authorize?client_id=...&redirect_uri=...&state=...
   ↓
3. 사용자가 Authorization Server에서 로그인 및 권한 동의
   ↓
4. Authorization Server가 Authorization Code와 함께 Redirect
   http://localhost:8080/callback?code=...&state=...
   ↓
5. Client Backend가 Authorization Code를 Access Token으로 교환
   POST /token
   {
     code: "...",
     client_id: "client_backend",
     client_secret: "secret_backend"  ⭐ 백엔드에서만 사용
   }
   ↓
6. Authorization Server가 Access Token 발급
   {
     access_token: "...",
     token_type: "Bearer",
     expires_in: 3600
   }
   ↓
7. Client Backend가 Access Token으로 사용자 정보 조회
   GET /userinfo
   Authorization: Bearer {access_token}
   ↓
8. Resource Server가 사용자 정보 반환
   {
     name: "홍길동",
     email: "user1@example.com"
   }
   ↓
9. Client Backend가 사용자에게 프로필 페이지 표시
```

## 📁 파일 구조

```
client-backend/
├── app.py                      # Flask 애플리케이션
├── requirements.txt            # Python 의존성
├── templates/
│   ├── index.html             # 메인 페이지
│   ├── profile.html           # 사용자 프로필 페이지
│   └── error.html             # 에러 페이지
└── README.md                   # 이 파일
```

## 🔍 주요 엔드포인트

### GET /
메인 페이지

### GET /login
OAuth2 로그인 시작
- State 생성 (CSRF 방지)
- Authorization Server로 리다이렉트

### GET /callback
OAuth2 콜백 엔드포인트
- Authorization Code 받기
- State 검증
- Token 교환
- 사용자 정보 조회

### GET /profile
사용자 프로필 페이지 (로그인 필요)

### GET /logout
로그아웃 (세션 삭제)

### GET /api/test
API 테스트 엔드포인트
- Access Token으로 보호된 API 호출 예시

## 🔐 보안 특징

### 1. client_secret 보호
```python
# ✅ 백엔드에서만 사용 (클라이언트에 노출 안 됨)
CLIENT_SECRET = "secret_backend"

def exchange_code_for_token(code):
    data = {
        'client_secret': CLIENT_SECRET  # 서버 사이드에서만 사용
    }
```

### 2. State 파라미터 (CSRF 방지)
```python
# 로그인 시작 시 생성
state = secrets.token_urlsafe(32)
session['oauth_state'] = state

# 콜백에서 검증
if state != session.get('oauth_state'):
    return error("CSRF attack detected")
```

### 3. Redirect URI 검증
Authorization Server에서 등록된 URI만 허용

### 4. 세션 관리
```python
# 사용자 정보와 토큰을 서버 사이드 세션에 저장
session['access_token'] = token
session['user'] = user_info
```

## 🧪 테스트 시나리오

### Scenario 1: 정상 로그인
1. http://localhost:8080 접속
2. "OAuth2로 로그인" 클릭
3. Authorization Server 로그인 (user1/pass1)
4. 권한 승인
5. 프로필 페이지로 리다이렉트
6. 사용자 정보 및 Access Token 확인

### Scenario 2: 권한 거부
1. 로그인 시작
2. Authorization Server에서 "거부" 클릭
3. 에러 페이지 표시 확인

### Scenario 3: API 호출
1. 로그인 완료 후 프로필 페이지
2. "API 테스트" 버튼 클릭
3. Access Token으로 API 호출 성공 확인

### Scenario 4: 로그아웃
1. "로그아웃" 버튼 클릭
2. 세션 삭제 확인
3. 홈페이지로 리다이렉트

## 📊 Public Client와 비교

| 항목 | Confidential Client | Public Client |
|------|-------------------|---------------|
| **실행 환경** | 서버 (백엔드) | 브라우저/앱 (프론트엔드) |
| **client_secret** | ✅ 사용 (안전) | ❌ 사용 불가 (노출됨) |
| **PKCE** | 선택 사항 | 필수 |
| **Token 교환** | 서버 사이드 | 클라이언트 사이드 |
| **보안 수준** | 높음 | 중간 (PKCE로 보완) |
| **예시** | 웹 서버 애플리케이션 | SPA, 모바일 앱 |

## 💡 학습 포인트

### 1. client_secret의 중요성
- **Confidential Client**: 백엔드에서 안전하게 보관 가능
- **Public Client**: 코드가 노출되므로 사용 불가

### 2. Token 교환 위치
- **Confidential Client**: 백엔드에서 Token 교환
  ```python
  # 서버 사이드에서 실행
  response = requests.post('/token', data={
      'client_secret': CLIENT_SECRET  # ✅ 안전
  })
  ```

- **Public Client**: 브라우저에서 Token 교환
  ```javascript
  // 클라이언트 사이드에서 실행
  fetch('/token', {
      body: 'client_secret=...'  // ❌ 코드에 노출됨!
  })
  ```

### 3. State 파라미터
CSRF 공격 방지를 위해 필수:
1. 로그인 시작 시 랜덤 state 생성
2. 세션에 저장
3. 콜백에서 검증

## 🐛 문제 해결

### "Connection refused" 오류
```bash
# Authorization Server가 실행 중인지 확인
curl http://localhost:5000
```

### 포트가 이미 사용 중
```bash
lsof -i :8080
kill -9 <PID>
```

### Token 교환 실패
- Authorization Server 로그 확인
- client_id, client_secret 확인
- redirect_uri 일치 여부 확인

## 🔗 관련 파일

- Authorization Server: `../auth-server/`
- Public Client (SPA): `../client-spa/`
- 프로젝트 전체 가이드: `../README.md`

