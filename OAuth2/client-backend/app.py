"""
Confidential Client - 백엔드 웹 애플리케이션
client_secret을 안전하게 보관할 수 있는 서버 사이드 애플리케이션
"""
from flask import Flask, request, redirect, render_template, session, url_for, jsonify
import requests
import secrets
import os
import sys
from urllib.parse import urlencode

# config 모듈 import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import HOST_IP, AUTHORIZATION_SERVER, REDIRECT_URI_BACKEND

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# 세션 설정 (개발 환경용)
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False  # HTTPS가 아니므로 False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1시간

# OAuth2 설정
CLIENT_ID = "client_backend"
CLIENT_SECRET = "secret_backend"  # 백엔드에서 안전하게 보관
REDIRECT_URI = REDIRECT_URI_BACKEND
SCOPE = "profile email"


@app.route('/')
def index():
    """메인 페이지"""
    user = session.get('user')
    access_token = session.get('access_token')
    
    return render_template('index.html', 
                         user=user, 
                         logged_in=bool(user),
                         access_token=access_token)


@app.route('/login')
def login():
    """
    OAuth2 로그인 시작
    사용자를 Authorization Server로 리다이렉트
    """
    # CSRF 방지를 위한 state 생성
    state = secrets.token_urlsafe(32)
    session['oauth_state'] = state
    session.permanent = True  # 세션을 영구적으로 설정
    
    # Authorization 요청 파라미터
    params = {
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'response_type': 'code',
        'scope': SCOPE,
        'state': state
    }
    
    # Authorization Server의 /authorize 엔드포인트로 리다이렉트
    auth_url = f"{AUTHORIZATION_SERVER}/authorize?{urlencode(params)}"
    
    print(f"\n🚀 사용자를 Authorization Server로 리다이렉트")
    print(f"   State 생성: {state}")
    print(f"   URL: {auth_url}\n")
    
    return redirect(auth_url)


@app.route('/callback')
def callback():
    """
    OAuth2 콜백 엔드포인트
    Authorization Server가 Authorization Code와 함께 여기로 리다이렉트
    """
    # Authorization Code 받기
    code = request.args.get('code')
    state = request.args.get('state')
    error = request.args.get('error')
    
    # 에러 처리
    if error:
        error_description = request.args.get('error_description', 'Unknown error')
        print(f"\n❌ Authorization 실패: {error}")
        print(f"   설명: {error_description}\n")
        return render_template('error.html', 
                             error=error, 
                             error_description=error_description)
    
    # State 검증 (CSRF 방지)
    stored_state = session.get('oauth_state')
    print(f"\n🔍 State 검증:")
    print(f"   받은 state: {state}")
    print(f"   저장된 state: {stored_state}")
    print(f"   세션 ID: {session.get('_id', 'N/A')}")
    print(f"   세션 내용: {dict(session)}\n")
    
    if not state or state != stored_state:
        print(f"\n❌ State 불일치! CSRF 공격 가능성")
        return render_template('error.html', 
                             error="invalid_state", 
                             error_description=f"State parameter mismatch. Received: {state}, Expected: {stored_state}")
    
    # State 사용 완료 (일회용)
    session.pop('oauth_state', None)
    
    if not code:
        return render_template('error.html', 
                             error="missing_code", 
                             error_description="Authorization code not received")
    
    print(f"\n✅ Authorization Code 받음: {code[:20]}...")
    
    # Authorization Code를 Access Token으로 교환
    try:
        token_data = exchange_code_for_token(code)
        
        # 세션에 저장
        session['access_token'] = token_data['access_token']
        session['refresh_token'] = token_data.get('refresh_token')
        session['token_type'] = token_data.get('token_type', 'Bearer')
        
        print(f"\n✅ Access Token 받음: {token_data['access_token'][:20]}...")
        
        # 사용자 정보 가져오기
        user_info = get_user_info(token_data['access_token'])
        session['user'] = user_info
        
        print(f"\n✅ 사용자 정보 받음:")
        print(f"   이름: {user_info.get('name')}")
        print(f"   이메일: {user_info.get('email')}\n")
        
        return redirect(url_for('profile'))
        
    except Exception as e:
        print(f"\n❌ 토큰 교환 실패: {str(e)}\n")
        return render_template('error.html', 
                             error="token_exchange_failed", 
                             error_description=str(e))


def exchange_code_for_token(code):
    """
    Authorization Code를 Access Token으로 교환
    Confidential Client이므로 client_secret 사용
    """
    token_url = f"{AUTHORIZATION_SERVER}/token"
    
    # Token 요청 파라미터
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET  # ⭐ Confidential Client의 핵심
    }
    
    print(f"\n🔄 Token 교환 요청:")
    print(f"   URL: {token_url}")
    print(f"   Code: {code[:20]}...")
    print(f"   Client ID: {CLIENT_ID}")
    print(f"   Client Secret: {CLIENT_SECRET[:10]}... (백엔드에서 안전하게 사용)")
    
    # POST 요청
    response = requests.post(token_url, data=data)
    
    if response.status_code != 200:
        error_data = response.json()
        raise Exception(f"{error_data.get('error')}: {error_data.get('error_description')}")
    
    return response.json()


def get_user_info(access_token):
    """
    Access Token으로 사용자 정보 가져오기
    Resource Server의 /userinfo 엔드포인트 호출
    """
    userinfo_url = f"{AUTHORIZATION_SERVER}/userinfo"
    
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    
    print(f"\n🔄 사용자 정보 요청:")
    print(f"   URL: {userinfo_url}")
    print(f"   Token: {access_token[:20]}...")
    
    response = requests.get(userinfo_url, headers=headers)
    
    if response.status_code != 200:
        error_data = response.json()
        raise Exception(f"Failed to get user info: {error_data}")
    
    return response.json()


@app.route('/profile')
def profile():
    """사용자 프로필 페이지"""
    user = session.get('user')
    access_token = session.get('access_token')
    
    if not user:
        return redirect(url_for('index'))
    
    return render_template('profile.html', 
                         user=user, 
                         access_token=access_token)


@app.route('/logout')
def logout():
    """로그아웃"""
    session.clear()
    print(f"\n🚪 로그아웃 완료\n")
    return redirect(url_for('index'))


@app.route('/api/test')
def api_test():
    """
    API 테스트 엔드포인트
    Access Token으로 보호된 API 호출 예시
    """
    access_token = session.get('access_token')
    
    if not access_token:
        return jsonify({"error": "Not authenticated"}), 401
    
    try:
        user_info = get_user_info(access_token)
        return jsonify({
            "message": "API 호출 성공!",
            "user": user_info
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 401


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 Confidential Client 시작 (백엔드 웹앱)")
    print("="*60)
    print(f"\n🌐 HOST IP: {HOST_IP}")
    print("   💡 변경하려면: export HOST_IP=your_ip")
    print("\n📋 OAuth2 설정:")
    print(f"   Client ID: {CLIENT_ID}")
    print(f"   Client Secret: {CLIENT_SECRET} ✅ (백엔드에서 안전하게 보관)")
    print(f"   Redirect URI: {REDIRECT_URI}")
    print(f"   Authorization Server: {AUTHORIZATION_SERVER}")
    print("\n🌐 애플리케이션:")
    print(f"   http://{HOST_IP}:8080")
    print("\n💡 테스트:")
    print("   1. Authorization Server가 실행 중인지 확인")
    print(f"   2. http://{HOST_IP}:8080 접속")
    print("   3. '로그인' 버튼 클릭")
    print("   4. user1/pass1 로 로그인")
    print("\n" + "="*60 + "\n")
    
    app.run(host='0.0.0.0', port=8080, debug=True)

