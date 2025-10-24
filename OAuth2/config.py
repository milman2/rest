"""
OAuth2 프로젝트 공통 설정
환경 변수를 통해 HOST IP를 동적으로 설정
"""
import os
import socket

def get_host_ip():
    """
    HOST IP 가져오기
    1. 환경 변수 HOST_IP 확인
    2. 없으면 자동으로 네트워크 IP 감지
    3. 실패하면 localhost 사용
    """
    # 환경 변수에서 읽기
    host_ip = os.environ.get('HOST_IP')
    
    if host_ip:
        return host_ip
    
    # 자동 감지 시도
    try:
        # 외부 연결을 시도하여 로컬 IP 얻기
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        host_ip = s.getsockname()[0]
        s.close()
        return host_ip
    except Exception:
        # 실패 시 localhost 사용
        return "localhost"

# 전역 설정
HOST_IP = get_host_ip()

# 서버 URL들
AUTHORIZATION_SERVER = f"http://{HOST_IP}:5000"
CLIENT_BACKEND_URL = f"http://{HOST_IP}:8080"
CLIENT_SPA_URL = f"http://{HOST_IP}:8081"

# Redirect URI들
REDIRECT_URI_BACKEND = f"http://{HOST_IP}:8080/callback"
REDIRECT_URI_SPA = f"http://{HOST_IP}:8081/callback.html"

