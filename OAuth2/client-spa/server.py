"""
Public Client (SPA) - 간단한 Flask 서버
HTML 파일에 HOST IP 설정을 주입
"""
from flask import Flask, render_template_string
import os
import sys

# config 모듈 import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import HOST_IP, AUTHORIZATION_SERVER, REDIRECT_URI_SPA

app = Flask(__name__)

# HTML 파일 읽기 및 설정 주입
def load_html_with_config(filename):
    """HTML 파일을 읽어서 설정 값을 주입"""
    filepath = os.path.join(os.path.dirname(__file__), filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # JavaScript 설정 부분 교체
    config_js = f"""
        // OAuth2 설정 (서버에서 주입됨)
        const AUTHORIZATION_SERVER = '{AUTHORIZATION_SERVER}';
        const CLIENT_ID = 'client_spa';
        // const CLIENT_SECRET = null;  // ⚠️ Public Client는 secret 없음!
        const REDIRECT_URI = '{REDIRECT_URI_SPA}';
        const SCOPE = 'profile email';
"""
    
    # 기존 설정 부분을 찾아서 교체
    import re
    pattern = r"// OAuth2 설정.*?const SCOPE = '[^']+';"
    content = re.sub(pattern, config_js.strip(), content, flags=re.DOTALL)
    
    return content

@app.route('/')
def index():
    """메인 페이지"""
    return render_template_string(load_html_with_config('index.html'))

@app.route('/callback.html')
def callback():
    """콜백 페이지"""
    return render_template_string(load_html_with_config('callback.html'))

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 Public Client (SPA) 시작")
    print("="*60)
    print(f"\n🌐 HOST IP: {HOST_IP}")
    print("   💡 변경하려면: export HOST_IP=your_ip")
    print("\n📋 OAuth2 설정:")
    print("   Client ID: client_spa")
    print("   Client Type: Public (PKCE 사용)")
    print(f"   Redirect URI: {REDIRECT_URI_SPA}")
    print(f"   Authorization Server: {AUTHORIZATION_SERVER}")
    print("\n🌐 애플리케이션:")
    print(f"   http://{HOST_IP}:8081")
    print("\n💡 테스트:")
    print("   1. Authorization Server가 실행 중인지 확인")
    print(f"   2. http://{HOST_IP}:8081 접속")
    print("   3. F12 개발자 도구 열기")
    print("   4. '로그인' 버튼 클릭하여 PKCE 확인")
    print("\n" + "="*60 + "\n")
    
    app.run(host='0.0.0.0', port=8081, debug=True)

