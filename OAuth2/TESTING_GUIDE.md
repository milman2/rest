# OAuth2 학습 프로젝트 - 테스트 가이드

이 가이드는 OAuth2 프로젝트를 단계별로 테스트하는 방법을 설명합니다.

## 📋 준비사항

### 1. uv 및 Python 3.12 확인
```bash
# uv 설치 확인
uv --version

# uv가 없다면 설치
curl -LsSf https://astral.sh/uv/install.sh | sh

# Python 3.12 확인
python3.12 --version
```

### 2. HOST IP 설정 (중요!)

이 프로젝트는 **자동으로 HOST IP를 감지**합니다!

#### 자동 감지
기본적으로 서버가 네트워크 IP를 자동으로 감지합니다 (예: 192.168.50.135)

#### 수동 설정 (선택사항)
특정 IP를 사용하려면:
```bash
# Linux/Mac
export HOST_IP=192.168.50.135

# Windows
set HOST_IP=192.168.50.135

# 확인
echo $HOST_IP
```

#### localhost만 사용
네트워크 접근이 필요 없다면:
```bash
export HOST_IP=localhost
```

### 3. 포트 확인
다음 포트들이 사용 가능한지 확인:
- `5000` - Authorization Server
- `8080` - Confidential Client
- `8081` - Public Client (SPA)

```bash
# 포트 사용 중인지 확인 (Linux/Mac)
lsof -i :5000
lsof -i :8080
lsof -i :8081

# 포트 사용 중이면 종료
kill -9 <PID>
```

## 🚀 Step 1: Authorization Server 실행

### 1.1. 디렉토리 이동
```bash
cd /home/milman2/rest/OAuth2/auth-server
```

### 1.2. 가상환경 생성 및 활성화
```bash
uv venv --python 3.12
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

### 1.3. 의존성 설치
```bash
uv pip install -r requirements.txt
```

### 1.4. 서버 실행
```bash
python app.py
```

**예상 출력:**
```
============================================================
🚀 OAuth2 Authorization Server 시작
============================================================

📋 등록된 사용자:
   - user1 / pass1 (홍길동)
   - user2 / pass2 (김철수)

📋 등록된 클라이언트:
   - client_backend (Confidential Client)
   - client_spa (Public Client)

🌐 엔드포인트:
   - http://192.168.50.135:5000/authorize
   - http://192.168.50.135:5000/token
   - http://192.168.50.135:5000/userinfo

============================================================

 * Running on http://0.0.0.0:5000
```

### 1.5. 서버 상태 확인
**새 터미널 열기:**
```bash
# 서버 출력에 표시된 IP 사용
curl http://{HOST_IP}:5000/

curl http://192.168.50.135:5000/

curl -X GET "http://192.168.50.135:5000/authorize?client_id=client_backend&redirect_uri=http://192.168.50.135:8080/callback&response_type=code&scope=profile+email" 2>/dev/null | head -20

url -X POST "http://192.168.50.135:5000/token" -d "grant_type=authorization_code&code=invalid&client_id=client_backend" 2>/dev/null

curl -X GET "http://192.168.50.135:5000/userinfo" -H "Authorization: Bearer invalid_token" 2>/dev/null
```

**예상 응답:**
```json
{
  "service": "OAuth2 Authorization Server",
  "status": "running",
  "endpoints": {
    "authorize": "/authorize",
    "token": "/token",
    "userinfo": "/userinfo"
  }
}
```

✅ **체크포인트:** Authorization Server가 정상적으로 실행 중

---

## 🏢 Step 2: Confidential Client 테스트

### 2.1. 새 터미널 열기
```bash
cd /home/milman2/rest/OAuth2/client-backend
```

### 2.2. 가상환경 생성 및 활성화
```bash
uv venv --python 3.12
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

### 2.3. 의존성 설치
```bash
uv pip install -r requirements.txt
```

### 2.4. 서버 실행
```bash
python app.py
```

**예상 출력:**
```
============================================================
🚀 Confidential Client 시작 (백엔드 웹앱)
============================================================

📋 OAuth2 설정:
   Client ID: client_backend
   Client Secret: secret_backend ✅ (백엔드에서 안전하게 보관)
   Redirect URI: http://192.168.50.135:8080/callback
   Authorization Server: http://192.168.50.135:5000

🌐 애플리케이션:
   http://192.168.50.135:8080

💡 테스트:
   1. Authorization Server가 실행 중인지 확인
   2. http://192.168.50.135:8080 접속
   3. '로그인' 버튼 클릭
   4. user1/pass1 로 로그인

============================================================
```

#### Test
```shell
curl http://192.168.50.135:8080/ 2>/dev/null | grep -o "<h1>.*</h1>" | head -1

curl -s http://192.168.50.135:8080/ | grep -E "(Confidential|특징|로그인)" | head -10

```

### 2.5. 브라우저에서 테스트

#### 2.5.1. 메인 페이지 접속
```
http://192.168.50.135:8080
```

**확인사항:**
- [ ] "Confidential Client" 제목 표시
- [ ] "client_secret 안전하게 보관" 배지 표시
- [ ] 특징 4가지 표시
- [ ] "OAuth2로 로그인" 버튼 표시

#### 2.5.2. 로그인 버튼 클릭

**예상 동작:**
1. Authorization Server (http://192.168.50.135:5000)로 리다이렉트
2. 로그인 화면 표시
3. "Backend Web App에서 로그인을 요청했습니다" 메시지 확인

**백엔드 터미널에서 확인:**
```
🚀 사용자를 Authorization Server로 리다이렉트
   URL: http://192.168.50.135:5000/authorize?client_id=...
```

#### 2.5.3. 로그인
- **아이디**: `user1`
- **비밀번호**: `pass1`
- "로그인" 버튼 클릭

**Authorization Server 터미널에서 확인:**
```
127.0.0.1 - - [날짜] "POST /authorize HTTP/1.1" 200 -
```

#### 2.5.4. 권한 동의
**확인사항:**
- [ ] "홍길동" 프로필 표시
- [ ] "Backend Web App"에서 요청 메시지
- [ ] "프로필 정보", "이메일 주소" 권한 표시

"승인" 버튼 클릭

**Authorization Server 터미널에서 확인:**
```
✅ Authorization Code 발급:
   User: user1
   Client: client_backend
   Code: (코드값)
   PKCE: False
   Redirect: http://localhost:8080/callback?code=...
```

#### 2.5.5. 콜백 처리
자동으로 http://192.168.50.135:8080/callback 으로 리다이렉트

**백엔드 터미널에서 확인:**
```
✅ Authorization Code 받음: (코드값)

🔄 Token 교환 요청:
   URL: http://localhost:5000/token
   Code: (코드값)
   Client ID: client_backend
   Client Secret: secret_backend... (백엔드에서 안전하게 사용)
```

**Authorization Server 터미널에서 확인:**
```
✅ Access Token 발급:
   User: user1
   Client: client_backend
   Token: (토큰값)
```

**백엔드 터미널에서 확인:**
```
✅ Access Token 받음: (토큰값)

🔄 사용자 정보 요청:
   URL: http://192.168.50.135:5000/userinfo
   Token: (토큰값)

✅ 사용자 정보 받음:
   이름: 홍길동
   이메일: user1@example.com
```

#### 2.5.6. 프로필 페이지
**확인사항:**
- [ ] "로그인 성공" 제목 및 "인증됨" 배지
- [ ] 프로필 이미지 표시
- [ ] "홍길동" 이름 표시
- [ ] "user1@example.com" 이메일 표시
- [ ] Access Token 전체 내용 표시
- [ ] "홈으로", "API 테스트", "로그아웃" 버튼 표시

#### 2.5.7. API 테스트 버튼 클릭
**예상 결과:**
```
✅ API 호출 성공!

{
  "message": "API 호출 성공!",
  "user": {
    "sub": "user1",
    "name": "홍길동",
    "email": "user1@example.com",
    "profile_image": "..."
  }
}
```

#### 2.5.8. 로그아웃
"로그아웃" 버튼 클릭

**확인사항:**
- [ ] 메인 페이지로 리다이렉트
- [ ] 로그인 전 화면 표시

**백엔드 터미널에서 확인:**
```
🚪 로그아웃 완료
```

✅ **체크포인트:** Confidential Client 전체 플로우 정상 동작

---

## 📱 Step 3: Public Client (SPA) 테스트

### 3.1. 새 터미널 열기
```bash
cd /home/milman2/rest/OAuth2/client-spa
```

### 3.2. 가상환경 생성 및 서버 시작
```bash
uv venv --python 3.12
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
python server.py
```

**예상 출력:**
```
============================================================
🚀 Public Client (SPA) 시작
============================================================

🌐 HOST IP: {감지된 IP}
   💡 변경하려면: export HOST_IP=your_ip

📋 OAuth2 설정:
   Client ID: client_spa
   Client Type: Public (PKCE 사용)
   Redirect URI: http://{HOST_IP}:8081/callback.html
   Authorization Server: http://{HOST_IP}:5000

🌐 애플리케이션:
   http://{HOST_IP}:8081

💡 테스트:
   1. Authorization Server가 실행 중인지 확인
   2. http://{HOST_IP}:8081 접속
   3. F12 개발자 도구 열기
   4. '로그인' 버튼 클릭하여 PKCE 확인

============================================================

 * Running on http://0.0.0.0:8081
```

### 3.3. 브라우저에서 테스트

#### 3.3.1. 메인 페이지 접속 + 개발자 도구 열기
```
http://192.168.50.135:8081
```

**F12 키를 눌러 개발자 도구 열기**
- Console 탭 선택

**확인사항:**
- [ ] "Public Client (SPA)" 제목 표시
- [ ] "client_secret 없음", "PKCE 사용" 배지 표시
- [ ] 특징 4가지 표시
- [ ] PKCE 설명 박스 표시
- [ ] "OAuth2로 로그인 (PKCE)" 버튼 표시

#### 3.3.2. 로그인 버튼 클릭

**Console에서 확인:**
```
🚀 OAuth2 로그인 시작 (PKCE)
1️⃣ Code Verifier 생성: (64자 랜덤 문자열)
2️⃣ Code Challenge 생성: (Base64 URL 인코딩된 해시)
3️⃣ Authorization Server로 리다이렉트
   Code Challenge 포함: (해시값)
```

**확인사항:**
- [ ] PKCE 생성 과정 섹션이 화면에 표시됨
- [ ] Code Verifier 표시 (길이 64자)
- [ ] Code Challenge 표시 (다른 값)
- [ ] Authorization Server로 리다이렉트

**Network 탭에서 확인:**
- `/authorize` 요청
- URL 파라미터에 `code_challenge`, `code_challenge_method=S256` 포함

#### 3.3.3. 로그인
- **아이디**: `user2`
- **비밀번호**: `pass2`
- "로그인" 버튼 클릭

**Authorization Server 터미널에서 확인:**
```
✅ Authorization Code 발급:
   User: user2
   Client: client_spa
   Code: (코드값)
   PKCE: True  ← ⭐ PKCE 사용됨
```

#### 3.3.4. 권한 동의
**확인사항:**
- [ ] "김철수" 프로필 표시
- [ ] "SPA Application"에서 요청 메시지

"승인" 버튼 클릭

#### 3.3.5. 콜백 처리 (callback.html)
자동으로 http://192.168.50.135:8081/callback.html 로 리다이렉트

**화면에서 확인:**
- [ ] 로딩 스피너 표시
- [ ] "OAuth2 콜백 처리 중..." 제목
- [ ] 4단계 진행 과정:
  1. ✅ Authorization Code 받음
  2. ✅ Code Verifier 확인
  3. ✅ Access Token 받음 (진행 중)
  4. ⏳ 사용자 정보 조회 중...

**Console에서 확인:**
```
✅ Authorization Code 받음: (코드값)
✅ State 검증 완료
✅ Code Verifier 확인: (64자 문자열)
🔄 Token 교환 시작 (PKCE)
```

**Network 탭에서 확인:**
- `/token` POST 요청
- Body에 `code_verifier` 포함
- Body에 `client_secret` **없음** ⭐

**Authorization Server 터미널에서 확인:**
```
✅ PKCE 검증 성공!
   Code Verifier: (64자 문자열)
   Code Challenge: (해시값)

✅ Access Token 발급:
   User: user2
   Client: client_spa
   Token: (토큰값)

✅ UserInfo 요청:
   User: user2
   Scopes: ['profile', 'email']
```

**Console에서 확인:**
```
✅ Access Token 받음: (토큰값)
🔄 사용자 정보 요청
✅ 사용자 정보 받음: {...}
```

#### 3.3.6. 프로필 페이지
1~2초 후 자동으로 index.html로 리다이렉트

**확인사항:**
- [ ] "로그인 성공!" 제목
- [ ] "PKCE 검증 완료" 서브타이틀
- [ ] "김철수" 프로필 카드
- [ ] "user2@example.com" 이메일
- [ ] Access Token 전체 내용
- [ ] "로그아웃" 버튼

**Application 탭에서 확인:**
(F12 → Application → Local Storage → http://192.168.50.135:8081)
- `access_token` 저장됨
- `user_info` 저장됨
- `code_verifier` 삭제됨 (일회용!)
- `oauth_state` 삭제됨 (일회용!)

#### 3.3.7. 로그아웃
"로그아웃" 버튼 클릭

**Console에서 확인:**
```
🚪 로그아웃 완료
```

**확인사항:**
- [ ] 로그인 전 화면으로 변경
- [ ] LocalStorage 모두 삭제됨

✅ **체크포인트:** Public Client (PKCE) 전체 플로우 정상 동작

---

## 🧪 고급 테스트 시나리오

### Scenario A: PKCE 없이 시도 (Public Client에서 실패 확인)

**목적:** PKCE의 중요성 이해

1. http://192.168.50.135:8081 접속
2. F12 → Console
3. 다음 코드 실행:
```javascript
// code_challenge 없이 Authorization 요청
const params = new URLSearchParams({
    client_id: 'client_spa',
    redirect_uri: 'http://192.168.50.135:8081/callback.html',
    response_type: 'code',
    scope: 'profile email'
    // code_challenge 없음!
});
window.location.href = `http://192.168.50.135:5000/authorize?${params}`;
```

**예상 결과:**
```json
{
  "error": "invalid_request",
  "error_description": "PKCE required for public clients"
}
```

✅ **학습 포인트:** Public Client는 PKCE 필수!

### Scenario B: 잘못된 Code Verifier (PKCE 검증 실패)

**목적:** PKCE 검증 메커니즘 이해

1. http://192.168.50.135:8081 접속
2. 로그인 시작 (정상 플로우)
3. Authorization Code 받은 후, callback.html에서
4. F12 → Console에서 다음 실행:
```javascript
// Code Verifier 변조
localStorage.setItem('code_verifier', 'wrong_verifier_12345');
```
5. 페이지 새로고침 (콜백 재시도)

**예상 결과:**
Authorization Server에서:
```
❌ PKCE 검증 실패!
   Code Verifier: wrong_verifier_12345
   Code Challenge: (원래 저장된 해시)
```

응답:
```json
{
  "error": "invalid_grant",
  "error_description": "PKCE verification failed"
}
```

✅ **학습 포인트:** Code Verifier가 틀리면 Token 발급 불가!

### Scenario C: 권한 거부

**목적:** 사용자가 권한을 거부하는 경우

1. 로그인 시작 (Confidential 또는 Public)
2. 로그인 완료
3. 권한 동의 화면에서 **"거부"** 버튼 클릭

**예상 결과:**
콜백 URL:
```
http://192.168.50.135:8080/callback?error=access_denied&error_description=User+denied+access
```

에러 페이지 표시

✅ **학습 포인트:** 사용자가 거부할 수 있음

### Scenario D: Redirect URI 불일치

**목적:** Redirect URI 검증의 중요성

1. F12 → Console
2. 다음 코드 실행 (잘못된 redirect_uri):
```javascript
const params = new URLSearchParams({
    client_id: 'client_backend',
    redirect_uri: 'http://evil.com/callback',  // ❌ 등록되지 않은 URI
    response_type: 'code',
    scope: 'profile email'
});
window.location.href = `http://192.168.50.135:5000/authorize?${params}`;
```

**예상 결과:**
```json
{
  "error": "invalid_request",
  "error_description": "Invalid redirect_uri"
}
```

✅ **학습 포인트:** Redirect URI 검증은 보안의 핵심!

### Scenario E: State 불일치 (CSRF 공격 시뮬레이션)

**목적:** State 파라미터의 중요성

1. Confidential Client에서 로그인 시작
2. Authorization Server 화면에서 URL 확인
3. URL의 state 파라미터 값을 다른 값으로 변경
4. 엔터

**예상 결과:**
```
❌ State 불일치! CSRF 공격 가능성
   받은 state: (변조된 값)
   저장된 state: (원래 값)
```

에러 페이지 표시

✅ **학습 포인트:** State 파라미터로 CSRF 방지!

---

## 📊 전체 플로우 비교

### Confidential Client
```
User → Client Backend → Auth Server (로그인)
                      ← Authorization Code
     → Client Backend → Auth Server (/token with client_secret)
                      ← Access Token
     → Client Backend → Resource Server (/userinfo)
                      ← User Data
     ← Client Backend (프로필 표시)
```

### Public Client (PKCE)
```
Browser: Code Verifier 생성
Browser: Code Challenge = SHA256(Verifier)
Browser → Auth Server (로그인 with Challenge)
        ← Authorization Code
Browser → Auth Server (/token with Verifier, NO secret)
        ← Access Token (PKCE 검증 후)
Browser → Resource Server (/userinfo)
        ← User Data
Browser: 프로필 표시
```

---

## ✅ 최종 체크리스트

### Authorization Server
- [ ] 서버 정상 실행 (포트 5000)
- [ ] 로그인 화면 표시
- [ ] 권한 동의 화면 표시
- [ ] Authorization Code 발급
- [ ] Access Token 발급 (Confidential)
- [ ] Access Token 발급 (PKCE)
- [ ] UserInfo 제공

### Confidential Client
- [ ] 서버 정상 실행 (포트 8080)
- [ ] OAuth2 로그인 플로우 완료
- [ ] client_secret 사용 확인
- [ ] State 파라미터 검증
- [ ] 프로필 페이지 표시
- [ ] API 테스트 성공
- [ ] 로그아웃 정상 동작

### Public Client (SPA)
- [ ] 서버 정상 실행 (포트 8081)
- [ ] PKCE Code Verifier 생성 확인
- [ ] PKCE Code Challenge 생성 확인
- [ ] OAuth2 로그인 플로우 완료
- [ ] PKCE 검증 성공
- [ ] client_secret 없이 Token 발급
- [ ] 프로필 페이지 표시
- [ ] LocalStorage 저장 확인
- [ ] 로그아웃 정상 동작

### 학습 목표 달성
- [ ] Authorization Code Flow 이해
- [ ] PKCE 메커니즘 이해
- [ ] Confidential vs Public Client 차이 이해
- [ ] Token 발급 과정 이해
- [ ] 보안 메커니즘 이해 (State, PKCE, Redirect URI)

---

## 🎓 다음 단계

이 프로젝트를 완료했다면:

1. **Refresh Token 구현** 추가
2. **JWT** 사용으로 변경
3. **Redis**로 Token 저장소 변경
4. **실제 서비스** 연동 (Google, GitHub OAuth2)
5. **OpenID Connect (OIDC)** 학습

---

## 🐛 문제 발생 시

### 모든 서버 종료
```bash
# 포트 사용 프로세스 찾기
lsof -i :5000
lsof -i :8080
lsof -i :8081

# 모두 종료
kill -9 <PID1> <PID2> <PID3>
```

### 처음부터 다시 시작
```bash
# 모든 터미널 닫기
# Step 1부터 다시 시작
```

### 로그 확인
각 서버의 터미널에서 실시간 로그를 확인하세요.
모든 주요 이벤트가 로깅됩니다.

---

**축하합니다! 🎉**

OAuth2의 핵심 개념을 직접 구현하면서 학습했습니다.
이제 실제 애플리케이션에 OAuth2를 적용할 준비가 되었습니다!

