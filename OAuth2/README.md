# OAuth2 학습 프로젝트

OAuth2를 직접 구현하면서 배우는 실습 프로젝트입니다.

## 📚 학습 목표

1. OAuth2 Authorization Code Flow 이해
2. PKCE (Proof Key for Code Exchange) 이해
3. Authorization Server 구현
4. Confidential Client vs Public Client 차이 체험
5. Token 발급 및 검증 메커니즘 이해

## 🏗️ 프로젝트 구조

```
OAuth2/
├── OAuth2.md                    # OAuth2 이론 및 시퀀스 다이어그램
├── README.md                    # 이 파일
├── TESTING_GUIDE.md            # 📘 상세 테스트 가이드 ⭐
├── auth-server/                 # Authorization Server + Resource Server
│   ├── app.py                   # Flask 서버
│   ├── requirements.txt         # Python 의존성
│   ├── database.py              # 간단한 인메모리 DB
│   ├── templates/               # 로그인/동의 화면
│   └── README.md                # 실행 가이드
├── client-backend/              # Confidential Client (백엔드 웹앱)
│   ├── app.py                   # Flask 클라이언트
│   ├── requirements.txt
│   ├── templates/               # UI
│   └── README.md
└── client-spa/                  # Public Client (SPA with PKCE)
    ├── index.html               # 메인 페이지 + PKCE 구현
    ├── callback.html            # OAuth2 콜백 페이지
    └── README.md
```

## 🎭 역할 설명

### 1. Authorization Server (포트: 5000)
- **역할**: Google, Facebook 같은 인증 제공자
- **기능**:
  - 사용자 로그인 화면 제공
  - 권한 동의 화면 제공
  - Authorization Code 발급
  - Access Token 발급 (PKCE 검증 포함)
  - Token 검증 API

### 2. Resource Server (포트: 5000, auth-server와 통합)
- **역할**: 사용자 데이터를 제공하는 API 서버
- **기능**:
  - `/userinfo` 엔드포인트
  - Access Token 검증

### 3. Client Backend (포트: 8080)
- **역할**: Confidential Client - 전통적인 웹 애플리케이션
- **특징**:
  - `client_secret` 사용
  - 백엔드에서 Token 교환
  - Authorization Code Flow

### 4. Client SPA (포트: 8081)
- **역할**: Public Client - Single Page Application
- **특징**:
  - `client_secret` 없음
  - PKCE 사용
  - 브라우저에서 직접 Token 교환

## 🚀 빠른 시작

> 💡 **상세한 테스트 가이드**: [TESTING_GUIDE.md](./TESTING_GUIDE.md)에서 단계별 설명, 예상 출력, 고급 시나리오를 확인하세요!

## 🚀 실행 순서

### 1단계: Authorization Server 실행
```bash
cd auth-server
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```
→ http://localhost:5000 에서 실행됨

### 2단계: Confidential Client 테스트
```bash
cd client-backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```
→ http://localhost:8080 에서 실행됨
→ 브라우저에서 로그인 테스트

### 3단계: Public Client (SPA) 테스트
```bash
cd client-spa
python3 -m http.server 8081
```
→ http://localhost:8081 에서 실행됨
→ 브라우저에서 PKCE 플로우 테스트

## 🔐 테스트 계정

Authorization Server에 미리 등록된 테스트 계정:

| 사용자 | 비밀번호 | 설명 |
|--------|---------|------|
| user1  | pass1   | 일반 사용자 |
| user2  | pass2   | 일반 사용자 |

## 📝 등록된 클라이언트

| Client ID | Client Secret | Type | Redirect URI |
|-----------|--------------|------|--------------|
| client_backend | secret_backend | Confidential | http://localhost:8080/callback |
| client_spa | (없음) | Public | http://localhost:8081/callback.html |

## 🧪 테스트 시나리오

### 기본 테스트

#### Scenario 1: Confidential Client 테스트
1. http://localhost:8080 접속
2. "OAuth2로 로그인" 버튼 클릭
3. Authorization Server 로그인 화면으로 리다이렉트
4. user1/pass1 입력
5. 권한 동의
6. 콜백으로 돌아와서 사용자 정보 표시

#### Scenario 2: Public Client (PKCE) 테스트
1. http://localhost:8081 접속
2. 개발자 도구(F12) 콘솔에서 PKCE 과정 확인
3. "OAuth2로 로그인 (PKCE)" 버튼 클릭
4. Authorization Server 로그인
5. PKCE 검증 과정 확인
6. 사용자 정보 표시

### 고급 테스트 시나리오

더 많은 테스트 시나리오는 **[TESTING_GUIDE.md](./TESTING_GUIDE.md)**를 참고하세요:

- ✅ PKCE 없이 시도 (실패 확인)
- ✅ 잘못된 Code Verifier (검증 실패)
- ✅ 권한 거부 테스트
- ✅ Redirect URI 불일치
- ✅ State 불일치 (CSRF 시뮬레이션)
- ✅ 전체 플로우 비교 및 분석

## 📊 학습 체크리스트

- [ ] Authorization Code가 URL에 어떻게 전달되는지 확인
- [ ] Access Token이 어떻게 발급되는지 확인
- [ ] Confidential Client는 client_secret을 사용하는 것 확인
- [ ] Public Client는 PKCE를 사용하는 것 확인
- [ ] Code Verifier와 Code Challenge의 관계 이해
- [ ] Redirect URI 검증의 중요성 이해
- [ ] Token으로 API를 호출하는 방법 확인
- [ ] Token 만료 시 동작 확인

## 🔍 디버깅 팁

1. **브라우저 개발자 도구 활용**
   - Network 탭에서 모든 요청 확인
   - Console에서 PKCE 생성 과정 확인

2. **서버 로그 확인**
   - Authorization Server 터미널에서 모든 요청 로그 확인
   - Token 검증 과정 확인

3. **URL 파라미터 확인**
   - Authorization 요청의 파라미터들
   - Callback URL의 code 파라미터

## 📚 참고 자료

- [RFC 6749 - OAuth 2.0](https://datatracker.ietf.org/doc/html/rfc6749)
- [RFC 7636 - PKCE](https://datatracker.ietf.org/doc/html/rfc7636)
- [OAuth2.md](./OAuth2.md) - 이론 및 시퀀스 다이어그램

## 🛠️ 기술 스택

- **Backend**: Python 3.8+, Flask
- **Frontend**: Vanilla JavaScript (의존성 없이 학습)
- **Storage**: 인메모리 (실습용, 실제 운영에서는 DB 사용)

## 💡 다음 단계 학습

이 프로젝트를 완료한 후:
1. Refresh Token 구현 추가
2. JWT 대신 Opaque Token 사용해보기
3. Redis로 Token 저장소 변경
4. OpenID Connect (OIDC) 추가 구현
5. 실제 서비스 (Google, GitHub) OAuth2 연동

---

**시작**: `auth-server` 부터 구현을 시작합니다!

