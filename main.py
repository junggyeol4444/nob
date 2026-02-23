"""NovelWriter Local — 애플리케이션 엔트리 포인트"""
import sys
import os

# src 디렉토리를 패키지로 참조할 수 있도록 경로 추가
sys.path.insert(0, os.path.dirname(__file__))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from src.database.db_manager import DatabaseManager
from src.gui.main_window import MainWindow
from src.utils import config


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("NovelWriter Local")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("NovelWriter")

    # 고DPI 지원
    app.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    # 데이터베이스 초기화
    cfg = config.load_config()
    db_path = cfg.get("db_path") or config.get_default_db_path()
    db = DatabaseManager(db_path)

    # 메인 윈도우 실행
    window = MainWindow(db)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
