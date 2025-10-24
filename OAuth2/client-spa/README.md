# Public Client - SPA with PKCE

브라우저에서 직접 실행되는 Single Page Application입니다. `client_secret`을 사용할 수 없으므로 PKCE를 사용합니다.

## 🎯 특징

- ✅ **Public Client** - `client_secret` 없이 동작
- ✅ **PKCE (Proof Key for Code Exchange)** - 보안 강화
- ✅ **브라우저에서 직접 Token 교환** - 백엔드 불필요
- ✅ **Vanilla JavaScript** - 프레임워크 없이 학습에 최적화
- ✅ **LocalStorage** - 클라이언트 사이드 데이터 저장

## 📦 OAuth2 설정

```javascript
const CLIENT_ID = "client_spa";
// const CLIENT_SECRET = null;  // ⚠️ Public Client는 secret 없음!
const REDIRECT_URI = "http://localhost:8081/callback.html";
const AUTHORIZATION_SERVER = "http://localhost:5000";
```

## 🚀 실행 방법

### 1. Authorization Server가 실행 중인지 확인
```bash
# 다른 터미널에서
cd ../auth-server
source venv/bin/activate
python app.py
```

### 2. HTTP 서버 시작
```bash
cd client-spa

# Python 3 사용
python3 -m http.server 8081

# 또는 Node.js 사용
npx http-server -p 8081
```

### 3. 브라우저에서 테스트
```
http://localhost:8081
```

### 4. 개발자 도구(F12) 열기
콘솔에서 PKCE 과정을 실시간으로 확인할 수 있습니다!

## 🔐 PKCE 구현

### PKCE란?

**PKCE (Proof Key for Code Exchange, RFC 7636)**

Public Client는 코드가 브라우저에 노출되므로 `client_secret`을 안전하게 보관할 수 없습니다.
PKCE는 동적으로 생성된 값으로 보안을 강화합니다.

### PKCE 동작 방식

```
1. Code Verifier 생성
   ↓
   랜덤 문자열 (43~128자)
   예: "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"
   
2. Code Challenge 생성
   ↓
   SHA256(Code Verifier) → Base64 URL Encoding
   예: "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM"
   
3. Authorization 요청 (Challenge 전송)
   ↓
   /authorize?code_challenge=E9Melhoa...&code_challenge_method=S256
   
4. Authorization Code 받음
   ↓
   
5. Token 요청 (Verifier 전송)
   ↓
   /token?code_verifier=dBjftJeZ...
   
6. 서버가 검증
   ↓
   SHA256(code_verifier) == stored_code_challenge ?
   
7. ✅ 검증 성공 → Access Token 발급
```

### PKCE 코드 구현

#### 1. Code Verifier 생성
```javascript
function generateRandomString(length) {
    const charset = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~';
    let result = '';
    const randomValues = new Uint8Array(length);
    crypto.getRandomValues(randomValues);  // 암호학적으로 안전한 난수
    
    for (let i = 0; i < length; i++) {
        result += charset[randomValues[i] % charset.length];
    }
    
    return result;
}

const codeVerifier = generateRandomString(64);
```

#### 2. Code Challenge 생성 (SHA256)
```javascript
async function sha256(plain) {
    const encoder = new TextEncoder();
    const data = encoder.encode(plain);
    const hash = await crypto.subtle.digest('SHA-256', data);
    return hash;
}

function base64UrlEncode(arrayBuffer) {
    const bytes = new Uint8Array(arrayBuffer);
    let binary = '';
    for (let i = 0; i < bytes.length; i++) {
        binary += String.fromCharCode(bytes[i]);
    }
    const base64 = btoa(binary);
    return base64
        .replace(/\+/g, '-')
        .replace(/\//g, '_')
        .replace(/=/g, '');
}

async function generateCodeChallenge(codeVerifier) {
    const hashed = await sha256(codeVerifier);
    return base64UrlEncode(hashed);
}

const codeChallenge = await generateCodeChallenge(codeVerifier);
```

#### 3. Authorization 요청 (Challenge 전송)
```javascript
const params = new URLSearchParams({
    client_id: CLIENT_ID,
    redirect_uri: REDIRECT_URI,
    response_type: 'code',
    scope: 'profile email',
    code_challenge: codeChallenge,        // ⭐ Challenge 전송
    code_challenge_method: 'S256'         // SHA256 사용
});

window.location.href = `${AUTHORIZATION_SERVER}/authorize?${params}`;
```

#### 4. Token 교환 (Verifier 전송)
```javascript
const tokenResponse = await fetch(`${AUTHORIZATION_SERVER}/token`, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
    },
    body: new URLSearchParams({
        grant_type: 'authorization_code',
        code: authorizationCode,
        redirect_uri: REDIRECT_URI,
        client_id: CLIENT_ID,
        code_verifier: codeVerifier  // ⭐ Verifier 전송 (secret 대신!)
    })
});
```

## 🔄 OAuth2 플로우

```
1. 사용자가 "로그인" 버튼 클릭
   ↓
2. 브라우저에서 Code Verifier 생성 (랜덤 문자열)
   ↓
3. Code Challenge 생성 (SHA256 해싱)
   ↓
4. LocalStorage에 Code Verifier 저장
   ↓
5. Authorization Server로 리다이렉트 (Challenge 포함)
   GET /authorize?code_challenge=...
   ↓
6. 사용자 로그인 및 권한 동의
   ↓
7. Authorization Code와 함께 callback.html로 리다이렉트
   ↓
8. callback.html에서:
   - Authorization Code 추출
   - LocalStorage에서 Code Verifier 가져오기
   - Token 엔드포인트에 Verifier 포함하여 요청
   ↓
9. Authorization Server:
   - SHA256(code_verifier) == code_challenge 검증
   - ✅ 성공 → Access Token 발급
   ↓
10. Access Token으로 사용자 정보 조회
    ↓
11. 프로필 화면 표시
```

## 📁 파일 구조

```
client-spa/
├── index.html          # 메인 페이지 (로그인 화면 + PKCE 구현)
├── callback.html       # OAuth2 콜백 페이지 (Token 교환)
└── README.md          # 이 파일
```

## 🧪 테스트 시나리오

### Scenario 1: PKCE로 정상 로그인
1. http://localhost:8081 접속
2. F12 개발자 도구 열기 (Console 탭)
3. "OAuth2로 로그인" 버튼 클릭
4. Console에서 Code Verifier, Code Challenge 확인
5. Authorization Server에서 로그인 (user1/pass1)
6. 권한 승인
7. callback.html에서 PKCE 검증 과정 확인
8. 프로필 화면 표시 확인

### Scenario 2: PKCE 검증 실패 테스트
1. 로그인 시작
2. Authorization Code 받은 후
3. LocalStorage에서 code_verifier 삭제:
   ```javascript
   localStorage.removeItem('code_verifier');
   ```
4. Token 요청 실패 확인
5. → **PKCE의 중요성 학습!**

### Scenario 3: Network 분석
1. F12 → Network 탭
2. 로그인 플로우 실행
3. 다음 요청들 확인:
   - `/authorize` 요청 (code_challenge 파라미터)
   - `/token` 요청 (code_verifier 파라미터)
   - `/userinfo` 요청 (Authorization 헤더)

## 🔍 디버깅

### Console 로그 확인
```
🚀 OAuth2 로그인 시작 (PKCE)
1️⃣ Code Verifier 생성: dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk
2️⃣ Code Challenge 생성: E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM
3️⃣ Authorization Server로 리다이렉트
✅ Authorization Code 받음: abc123...
✅ Code Verifier 확인: dBjftJeZ...
✅ Access Token 받음: xyz789...
✅ 사용자 정보 받음: { name: "홍길동", ... }
```

### LocalStorage 확인
F12 → Application → Local Storage → http://localhost:8081

저장된 항목:
- `code_verifier` - PKCE Code Verifier (임시)
- `oauth_state` - CSRF 방지 State (임시)
- `access_token` - Access Token
- `user_info` - 사용자 정보

## 📊 Confidential Client와 비교

| 항목 | Public Client (SPA) | Confidential Client |
|------|---------------------|---------------------|
| **실행 환경** | 브라우저 | 서버 (백엔드) |
| **client_secret** | ❌ 없음 | ✅ 있음 |
| **PKCE** | ✅ 필수 | 선택 사항 |
| **Token 교환** | 브라우저에서 직접 | 백엔드에서 |
| **코드 노출** | ⚠️ 전체 노출 | ✅ 서버만 |
| **보안 수준** | 중간 (PKCE로 보완) | 높음 |

## 💡 보안 고려사항

### ✅ 구현된 보안 기능
1. **PKCE** - Authorization Code 탈취 방지
2. **State 파라미터** - CSRF 공격 방지
3. **crypto.getRandomValues()** - 암호학적으로 안전한 난수

### ⚠️ 실제 운영 시 추가 필요
1. **HTTPS 필수** - HTTP는 중간자 공격에 취약
2. **Token 저장** - LocalStorage 대신 HttpOnly Cookie 고려
3. **XSS 방지** - Content Security Policy 설정
4. **Token 만료** - Refresh Token 구현
5. **로그아웃** - Token 서버에서 폐기

## 🎓 학습 포인트

### 1. PKCE의 필요성
```javascript
// ❌ Public Client가 client_secret 사용하면
const secret = "my_secret";  // 브라우저 코드에 노출!

// ✅ PKCE 사용
const verifier = generateRandomString(64);  // 매번 새로 생성
const challenge = await sha256(verifier);   // 해시값만 전송
```

### 2. Code Verifier의 일회성
- 매 로그인마다 새로 생성
- Authorization Code도 일회용
- 중간자가 탈취해도 Verifier 없으면 Token 발급 불가

### 3. SHA256의 역할
- Code Challenge → 서버 저장 (공개)
- Code Verifier → 클라이언트 보관 (비공개)
- SHA256은 단방향 (Challenge에서 Verifier 복원 불가)

## 🐛 문제 해결

### CORS 오류
Authorization Server에서 CORS를 허용했는지 확인

### "Code Verifier를 찾을 수 없습니다"
1. LocalStorage 확인
2. 브라우저 시크릿 모드에서는 LocalStorage가 지워질 수 있음
3. 다시 로그인 시도

### Token 교환 실패
1. F12 → Network 탭에서 /token 요청 확인
2. code_verifier가 전송되었는지 확인
3. Authorization Server 로그 확인

## 🔗 관련 파일

- Authorization Server: `../auth-server/`
- Confidential Client: `../client-backend/`
- 프로젝트 전체 가이드: `../README.md`
- OAuth2.md: `../OAuth2.md` (이론 및 시퀀스 다이어그램)

## 📚 참고 자료

- [RFC 7636 - PKCE](https://datatracker.ietf.org/doc/html/rfc7636)
- [OAuth 2.0 for Browser-Based Apps](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-browser-based-apps)

