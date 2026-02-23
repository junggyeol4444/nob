"""NovelWriter Local — 웹 애플리케이션 실행 스크립트"""
import os
import sys

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(__file__))

from web_app import socketio, app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    # allow_unsafe_werkzeug is needed for the development server with threading mode
    print(f"NovelWriter Local 시작 중...")
    print(f"브라우저에서 http://localhost:{port} 에 접속하세요")
    socketio.run(app, host="0.0.0.0", port=port, debug=debug, allow_unsafe_werkzeug=not debug)
