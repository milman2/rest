"""
OAuth2 Authorization Server + Resource Server
Google, Facebook과 같은 인증 제공자 역할
"""
from flask import Flask, request, render_template, redirect, session, jsonify, url_for
import secrets
import os
import sys
from urllib.parse import urlencode, parse_qs
from datetime import datetime

# config 모듈 import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import HOST_IP

from database import (
    verify_user, get_user, verify_client, get_client,
    verify_redirect_uri, generate_authorization_code,
    verify_authorization_code, generate_access_token,
    generate_refresh_token, verify_access_token,
    verify_code_challenge
)

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# 세션 설정 (개발 환경용)
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False  # HTTPS가 아니므로 False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1시간

# CORS 허용 (개발용)
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    return response


@app.route('/')
def index():
    """서버 상태 확인"""
    return jsonify({
        "service": "OAuth2 Authorization Server",
        "status": "running",
        "endpoints": {
            "authorize": "/authorize",
            "token": "/token",
            "userinfo": "/userinfo"
        }
    })


@app.route('/authorize', methods=['GET', 'POST'])
def authorize():
    """
    Authorization Endpoint
    1. 클라이언트가 사용자를 이 엔드포인트로 리다이렉트
    2. 사용자 로그인 처리
    3. 권한 동의 처리
    4. Authorization Code 발급
    """
    
    if request.method == 'GET':
        # Step 1: 클라이언트로부터 받은 파라미터 검증
        client_id = request.args.get('client_id')
        redirect_uri = request.args.get('redirect_uri')
        response_type = request.args.get('response_type', 'code')
        scope = request.args.get('scope', 'profile email')
        state = request.args.get('state')  # CSRF 방지용
        
        # PKCE 파라미터 (Public Client용)
        code_challenge = request.args.get('code_challenge')
        code_challenge_method = request.args.get('code_challenge_method', 'S256')
        
        # 필수 파라미터 검증
        if not client_id or not redirect_uri:
            return jsonify({"error": "invalid_request", "error_description": "Missing required parameters"}), 400
        
        # 클라이언트 검증
        client = get_client(client_id)
        if not client:
            return jsonify({"error": "invalid_client", "error_description": "Unknown client"}), 401
        
        # Redirect URI 검증 (보안상 매우 중요!)
        if not verify_redirect_uri(client_id, redirect_uri):
            return jsonify({"error": "invalid_request", "error_description": "Invalid redirect_uri"}), 400
        
        # Response type 검증 (현재는 code만 지원)
        if response_type != 'code':
            return jsonify({"error": "unsupported_response_type"}), 400
        
        # Public Client는 PKCE 필수
        if client["client_type"] == "public" and not code_challenge:
            return jsonify({"error": "invalid_request", "error_description": "PKCE required for public clients"}), 400
        
        # 세션에 요청 정보 저장
        session['auth_request'] = {
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'scope': scope,
            'state': state,
            'code_challenge': code_challenge,
            'code_challenge_method': code_challenge_method
        }
        session.permanent = True  # 세션을 영구적으로 설정
        
        # 로그인 화면 표시
        return render_template('login.html', client=client)
    
    elif request.method == 'POST':
        # Step 2: 로그인 처리
        username = request.form.get('username')
        password = request.form.get('password')
        
        # 세션 확인
        if 'auth_request' not in session:
            return jsonify({
                "error": "invalid_request",
                "error_description": "Session expired. Please restart the authorization flow."
            }), 400
        
        auth_request = session['auth_request']
        client = get_client(auth_request['client_id'])
        
        # 사용자 인증
        user_id = verify_user(username, password)
        if not user_id:
            return render_template('login.html', 
                                 client=client, 
                                 error="아이디 또는 비밀번호가 잘못되었습니다.")
        
        # 로그인 성공 - 세션에 사용자 정보 저장
        session['user_id'] = user_id
        
        # 권한 동의 화면으로 이동
        scopes = auth_request['scope'].split()
        
        return render_template('consent.html', 
                             client=client, 
                             scopes=scopes,
                             user=get_user(user_id))


@app.route('/consent', methods=['POST'])
def consent():
    """
    권한 동의 처리
    사용자가 권한을 승인하면 Authorization Code 발급
    """
    action = request.form.get('action')
    
    if action != 'approve':
        # 사용자가 거부함
        auth_request = session.get('auth_request', {})
        redirect_uri = auth_request.get('redirect_uri')
        state = auth_request.get('state')
        
        params = {
            'error': 'access_denied',
            'error_description': 'User denied access'
        }
        if state:
            params['state'] = state
        
        return redirect(f"{redirect_uri}?{urlencode(params)}")
    
    # 사용자가 승인함 - Authorization Code 발급
    user_id = session.get('user_id')
    auth_request = session.get('auth_request', {})
    
    if not user_id or not auth_request:
        return jsonify({"error": "invalid_session"}), 400
    
    # Authorization Code 생성
    code = generate_authorization_code(
        client_id=auth_request['client_id'],
        user_id=user_id,
        redirect_uri=auth_request['redirect_uri'],
        scopes=auth_request['scope'].split(),
        code_challenge=auth_request.get('code_challenge'),
        code_challenge_method=auth_request.get('code_challenge_method')
    )
    
    # 클라이언트로 리다이렉트 (Authorization Code 전달)
    params = {'code': code}
    if auth_request.get('state'):
        params['state'] = auth_request['state']
    
    redirect_url = f"{auth_request['redirect_uri']}?{urlencode(params)}"
    
    # 세션 정리
    session.pop('auth_request', None)
    session.pop('user_id', None)
    
    print(f"\n✅ Authorization Code 발급:")
    print(f"   User: {user_id}")
    print(f"   Client: {auth_request['client_id']}")
    print(f"   Code: {code[:20]}...")
    print(f"   PKCE: {bool(auth_request.get('code_challenge'))}")
    print(f"   Redirect: {redirect_url}\n")
    
    return redirect(redirect_url)


@app.route('/token', methods=['POST'])
def token():
    """
    Token Endpoint
    Authorization Code를 Access Token으로 교환
    """
    grant_type = request.form.get('grant_type')
    
    if grant_type != 'authorization_code':
        return jsonify({
            "error": "unsupported_grant_type",
            "error_description": "Only authorization_code is supported"
        }), 400
    
    # 파라미터 추출
    code = request.form.get('code')
    redirect_uri = request.form.get('redirect_uri')
    client_id = request.form.get('client_id')
    client_secret = request.form.get('client_secret')
    code_verifier = request.form.get('code_verifier')  # PKCE
    
    if not code or not redirect_uri or not client_id:
        return jsonify({
            "error": "invalid_request",
            "error_description": "Missing required parameters"
        }), 400
    
    # 클라이언트 검증
    client = get_client(client_id)
    if not client:
        return jsonify({"error": "invalid_client"}), 401
    
    # Confidential Client는 client_secret 필수
    if client["client_type"] == "confidential":
        if not verify_client(client_id, client_secret):
            return jsonify({"error": "invalid_client", "error_description": "Invalid client credentials"}), 401
    
    # Authorization Code 검증
    auth_code, error = verify_authorization_code(code, client_id, redirect_uri)
    if error:
        return jsonify({"error": "invalid_grant", "error_description": error}), 400
    
    # PKCE 검증 (Public Client)
    if auth_code.get('code_challenge'):
        if not code_verifier:
            return jsonify({
                "error": "invalid_request",
                "error_description": "code_verifier required"
            }), 400
        
        if not verify_code_challenge(
            code_verifier,
            auth_code['code_challenge'],
            auth_code.get('code_challenge_method', 'S256')
        ):
            print(f"\n❌ PKCE 검증 실패!")
            print(f"   Code Verifier: {code_verifier[:20]}...")
            print(f"   Code Challenge: {auth_code['code_challenge'][:20]}...\n")
            return jsonify({
                "error": "invalid_grant",
                "error_description": "PKCE verification failed"
            }), 400
        
        print(f"\n✅ PKCE 검증 성공!")
        print(f"   Code Verifier: {code_verifier[:20]}...")
        print(f"   Code Challenge: {auth_code['code_challenge'][:20]}...\n")
    
    # Access Token 생성
    access_token = generate_access_token(
        user_id=auth_code['user_id'],
        client_id=client_id,
        scopes=auth_code['scopes']
    )
    
    # Refresh Token 생성
    refresh_token = generate_refresh_token(
        user_id=auth_code['user_id'],
        client_id=client_id,
        scopes=auth_code['scopes']
    )
    
    print(f"\n✅ Access Token 발급:")
    print(f"   User: {auth_code['user_id']}")
    print(f"   Client: {client_id}")
    print(f"   Token: {access_token[:20]}...\n")
    
    # OAuth2 표준 응답
    return jsonify({
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": 3600,  # 1시간
        "refresh_token": refresh_token,
        "scope": " ".join(auth_code['scopes'])
    })


@app.route('/userinfo', methods=['GET'])
def userinfo():
    """
    Resource Server - UserInfo Endpoint
    Access Token으로 사용자 정보 조회
    """
    # Authorization 헤더에서 토큰 추출
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "invalid_token", "error_description": "Missing or invalid Authorization header"}), 401
    
    token = auth_header[7:]  # "Bearer " 제거
    
    # 토큰 검증
    token_data, error = verify_access_token(token)
    if error:
        return jsonify({"error": "invalid_token", "error_description": error}), 401
    
    # 사용자 정보 조회
    user = get_user(token_data['user_id'])
    if not user:
        return jsonify({"error": "user_not_found"}), 404
    
    # scope에 따라 반환할 정보 필터링
    scopes = token_data['scopes']
    response = {}
    
    if 'profile' in scopes:
        response['name'] = user['name']
        response['profile_image'] = user['profile_image']
    
    if 'email' in scopes:
        response['email'] = user['email']
    
    response['sub'] = user['username']  # subject (사용자 고유 ID)
    
    print(f"\n✅ UserInfo 요청:")
    print(f"   User: {user['username']}")
    print(f"   Scopes: {scopes}\n")
    
    return jsonify(response)


@app.route('/introspect', methods=['POST'])
def introspect():
    """
    Token Introspection Endpoint (RFC 7662)
    토큰의 유효성과 메타데이터 확인
    """
    token = request.form.get('token')
    if not token:
        return jsonify({"active": False}), 400
    
    token_data, error = verify_access_token(token)
    if error:
        return jsonify({"active": False})
    
    return jsonify({
        "active": True,
        "scope": " ".join(token_data['scopes']),
        "client_id": token_data['client_id'],
        "username": token_data['user_id'],
        "exp": int(token_data['expires_at'].timestamp())
    })


# ====================================
# Resource Server - 추가 보호된 API들
# ====================================

def require_token(required_scopes=None):
    """Access Token 검증 데코레이터"""
    from functools import wraps
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({"error": "unauthorized", "message": "Access token required"}), 401
            
            token = auth_header[7:]
            token_data, error = verify_access_token(token)
            if error:
                return jsonify({"error": "invalid_token", "message": error}), 401
            
            # Scope 검증
            if required_scopes:
                user_scopes = set(token_data['scopes'])
                if not any(scope in user_scopes for scope in required_scopes):
                    return jsonify({"error": "insufficient_scope", 
                                  "message": f"Required scopes: {required_scopes}"}), 403
            
            # 함수에 token_data 전달
            return f(token_data, *args, **kwargs)
        return decorated_function
    return decorator


@app.route('/api/posts', methods=['GET'])
@require_token(required_scopes=['profile'])
def get_posts(token_data):
    """
    사용자 게시물 조회 API
    Scope: profile 필요
    """
    from database import user_posts
    
    user_id = token_data['user_id']
    posts = user_posts.get(user_id, [])
    
    print(f"\n✅ 게시물 조회 요청:")
    print(f"   User: {user_id}")
    print(f"   게시물 수: {len(posts)}\n")
    
    return jsonify({
        "user": user_id,
        "total": len(posts),
        "posts": posts
    })


@app.route('/api/posts', methods=['POST'])
@require_token(required_scopes=['profile'])
def create_post(token_data):
    """
    게시물 작성 API
    Scope: profile 필요
    """
    from database import user_posts
    
    user_id = token_data['user_id']
    data = request.get_json()
    
    if not data or 'title' not in data or 'content' not in data:
        return jsonify({"error": "invalid_request", "message": "title and content required"}), 400
    
    # 새 게시물 생성
    if user_id not in user_posts:
        user_posts[user_id] = []
    
    new_post = {
        "id": len(user_posts[user_id]) + 1,
        "title": data['title'],
        "content": data['content'],
        "created_at": datetime.now().strftime("%Y-%m-%d")
    }
    
    user_posts[user_id].append(new_post)
    
    print(f"\n✅ 게시물 작성:")
    print(f"   User: {user_id}")
    print(f"   Title: {new_post['title']}\n")
    
    return jsonify(new_post), 201


@app.route('/api/settings', methods=['GET'])
@require_token(required_scopes=['profile'])
def get_settings(token_data):
    """
    사용자 설정 조회 API
    Scope: profile 필요
    """
    from database import user_settings
    
    user_id = token_data['user_id']
    settings = user_settings.get(user_id, {})
    
    return jsonify(settings)


@app.route('/api/settings', methods=['PUT'])
@require_token(required_scopes=['profile'])
def update_settings(token_data):
    """
    사용자 설정 업데이트 API
    Scope: profile 필요
    """
    from database import user_settings
    
    user_id = token_data['user_id']
    data = request.get_json()
    
    if user_id not in user_settings:
        user_settings[user_id] = {}
    
    user_settings[user_id].update(data)
    
    print(f"\n✅ 설정 업데이트:")
    print(f"   User: {user_id}")
    print(f"   Updated: {data}\n")
    
    return jsonify(user_settings[user_id])


@app.route('/api/stats', methods=['GET'])
@require_token(required_scopes=['profile'])
def get_stats(token_data):
    """
    사용자 통계 API
    Scope: profile 필요
    """
    from database import user_posts, user_settings
    
    user_id = token_data['user_id']
    posts = user_posts.get(user_id, [])
    
    stats = {
        "user": user_id,
        "total_posts": len(posts),
        "account_created": "2024-10-24",
        "last_login": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "scopes": token_data['scopes']
    }
    
    return jsonify(stats)


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 OAuth2 Authorization Server 시작")
    print("="*60)
    print("\n📋 등록된 사용자:")
    print("   - user1 / pass1 (홍길동)")
    print("   - user2 / pass2 (김철수)")
    print("\n📋 등록된 클라이언트:")
    print("   - client_backend (Confidential Client)")
    print("   - client_spa (Public Client)")
    print(f"\n🌐 HOST IP: {HOST_IP}")
    print("   💡 변경하려면: export HOST_IP=your_ip")
    print("\n🌐 엔드포인트:")
    print(f"   - http://{HOST_IP}:5000/authorize")
    print(f"   - http://{HOST_IP}:5000/token")
    print(f"   - http://{HOST_IP}:5000/userinfo")
    print("\n" + "="*60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)

