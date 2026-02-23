"""메인 애플리케이션 윈도우"""
import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QListWidget, QListWidgetItem, QPushButton, QLabel, QTabWidget,
    QMenuBar, QMenu, QStatusBar, QFileDialog, QMessageBox,
    QDialog, QFormLayout, QLineEdit, QComboBox, QDialogButtonBox,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QFont

from ..database.db_manager import DatabaseManager
from ..database.models import Project, Chapter
from ..ai.llm_client import LLMClient
from ..ai.context_manager import ContextManager
from ..utils import config
from .project_dialog import ProjectDialog
from .chapter_editor import ChapterEditor
from .character_panel import CharacterPanel
from .worldbuilding_panel import WorldBuildingPanel


class SettingsDialog(QDialog):
    """LLM 설정 다이얼로그"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("설정")
        self.setMinimumWidth(420)
        cfg = config.load_config()

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.endpoint_edit = QLineEdit(cfg.get("llm_endpoint", "http://localhost:11434"))
        form.addRow("LLM 엔드포인트", self.endpoint_edit)

        self.model_edit = QLineEdit(cfg.get("llm_model", "mistral"))
        form.addRow("모델 이름", self.model_edit)

        self.temp_edit = QLineEdit(str(cfg.get("temperature", 0.8)))
        form.addRow("Temperature", self.temp_edit)

        self.tokens_edit = QLineEdit(str(cfg.get("max_tokens", 4096)))
        form.addRow("Max Tokens", self.tokens_edit)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._save_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _save_and_accept(self):
        cfg = config.load_config()
        cfg["llm_endpoint"] = self.endpoint_edit.text().strip()
        cfg["llm_model"] = self.model_edit.text().strip()
        try:
            cfg["temperature"] = float(self.temp_edit.text())
        except ValueError:
            pass
        try:
            cfg["max_tokens"] = int(self.tokens_edit.text())
        except ValueError:
            pass
        config.save_config(cfg)
        self.accept()


class MainWindow(QMainWindow):
    """메인 윈도우"""

    def __init__(self, db: DatabaseManager):
        super().__init__()
        self.db = db
        self._current_project: Project = None
        self._context_manager: ContextManager = None

        self.setWindowTitle("NovelWriter Local")
        self.setMinimumSize(1100, 700)

        self._setup_menu()
        self._setup_central()
        self._setup_status_bar()
        self._refresh_project_list()
        self._init_llm()

    # ──────────────────────────────────────────
    # 메뉴바 구성
    # ──────────────────────────────────────────

    def _setup_menu(self):
        menubar = self.menuBar()

        # 파일 메뉴
        file_menu = menubar.addMenu("파일(&F)")
        self._add_action(file_menu, "새 프로젝트(&N)", self._new_project, "Ctrl+N")
        file_menu.addSeparator()

        export_menu = file_menu.addMenu("내보내기")
        self._add_action(export_menu, "현재 챕터 txt로 저장", self._export_chapter_txt)
        self._add_action(export_menu, "전체 챕터 txt로 저장", self._export_all_txt)
        self._add_action(export_menu, "전체 챕터 docx로 저장", self._export_docx)

        file_menu.addSeparator()
        self._add_action(file_menu, "종료(&Q)", self.close, "Ctrl+Q")

        # 편집 메뉴
        edit_menu = menubar.addMenu("편집(&E)")
        self._add_action(edit_menu, "프로젝트 편집", self._edit_project)
        self._add_action(edit_menu, "프로젝트 삭제", self._delete_project)

        # 도구 메뉴
        tools_menu = menubar.addMenu("도구(&T)")
        self._add_action(tools_menu, "설정", self._open_settings)
        self._add_action(tools_menu, "LLM 연결 확인", self._check_llm)

        # 도움말 메뉴
        help_menu = menubar.addMenu("도움말(&H)")
        self._add_action(help_menu, "정보", self._show_about)

    @staticmethod
    def _add_action(menu: QMenu, text: str, slot, shortcut: str = None) -> QAction:
        action = QAction(text, menu)
        action.triggered.connect(slot)
        if shortcut:
            action.setShortcut(shortcut)
        menu.addAction(action)
        return action

    # ──────────────────────────────────────────
    # 중앙 레이아웃 구성
    # ──────────────────────────────────────────

    def _setup_central(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # ── 왼쪽: 프로젝트 목록 ──
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(6, 6, 6, 6)

        left_layout.addWidget(QLabel("프로젝트"))
        self.project_list = QListWidget()
        self.project_list.currentItemChanged.connect(self._on_project_selected)
        self.project_list.itemDoubleClicked.connect(self._open_project)
        left_layout.addWidget(self.project_list)

        proj_btn_row = QHBoxLayout()
        new_btn = QPushButton("새 프로젝트")
        new_btn.clicked.connect(self._new_project)
        open_btn = QPushButton("열기")
        open_btn.clicked.connect(self._open_project)
        proj_btn_row.addWidget(new_btn)
        proj_btn_row.addWidget(open_btn)
        left_layout.addLayout(proj_btn_row)

        left_widget.setMaximumWidth(220)
        splitter.addWidget(left_widget)

        # ── 중앙: 챕터 편집기 ──
        self.chapter_editor = ChapterEditor(self.db)
        self.chapter_editor.chapter_saved.connect(self._on_chapter_saved)
        splitter.addWidget(self.chapter_editor)

        # ── 오른쪽: 탭 패널 ──
        right_tabs = QTabWidget()
        right_tabs.setMaximumWidth(280)

        self.character_panel = CharacterPanel(self.db)
        right_tabs.addTab(self.character_panel, "캐릭터")

        self.worldbuilding_panel = WorldBuildingPanel(self.db)
        right_tabs.addTab(self.worldbuilding_panel, "세계관")

        splitter.addWidget(right_tabs)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 3)
        splitter.setStretchFactor(2, 0)

        main_layout.addWidget(splitter)

    def _setup_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("NovelWriter Local 준비됨")

    # ──────────────────────────────────────────
    # LLM 초기화
    # ──────────────────────────────────────────

    def _init_llm(self):
        cfg = config.load_config()
        client = LLMClient(
            endpoint=cfg.get("llm_endpoint", "http://localhost:11434"),
            model=cfg.get("llm_model", "mistral"),
            temperature=cfg.get("temperature", 0.8),
            max_tokens=cfg.get("max_tokens", 4096),
        )
        self._context_manager = ContextManager(self.db, client)
        self.chapter_editor.set_context_manager(self._context_manager)

    # ──────────────────────────────────────────
    # 프로젝트 관련 액션
    # ──────────────────────────────────────────

    def _refresh_project_list(self):
        self.project_list.clear()
        projects = self.db.get_all_projects()
        for p in projects:
            item = QListWidgetItem(p.title)
            item.setData(Qt.ItemDataRole.UserRole, p)
            self.project_list.addItem(item)

    def _on_project_selected(self, current, previous):
        pass  # 더블클릭으로 열도록 유지

    def _new_project(self):
        dlg = ProjectDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            project = dlg.get_project_data()
            project.id = self.db.create_project(project)
            self._refresh_project_list()
            self._load_project(project)
            self.status_bar.showMessage(f"새 프로젝트 생성: {project.title}")

    def _open_project(self, item=None):
        if item is None:
            item = self.project_list.currentItem()
        if not item:
            QMessageBox.information(self, "알림", "프로젝트를 선택해주세요.")
            return
        project: Project = item.data(Qt.ItemDataRole.UserRole)
        self._load_project(project)

    def _load_project(self, project: Project):
        self._current_project = project
        self.setWindowTitle(f"NovelWriter Local — {project.title}")
        self.chapter_editor.set_project(project.id)
        self.character_panel.set_project(project.id)
        self.worldbuilding_panel.set_project(project.id)
        self.status_bar.showMessage(f"프로젝트 열림: {project.title} [{project.genre}]")

    def _edit_project(self):
        if not self._current_project:
            QMessageBox.information(self, "알림", "편집할 프로젝트를 먼저 열어주세요.")
            return
        dlg = ProjectDialog(self, self._current_project)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            updated = dlg.get_project_data()
            self.db.update_project(updated)
            self._current_project = updated
            self._refresh_project_list()
            self.setWindowTitle(f"NovelWriter Local — {updated.title}")
            self.status_bar.showMessage(f"프로젝트 정보 수정됨: {updated.title}")

    def _delete_project(self):
        if not self._current_project:
            QMessageBox.information(self, "알림", "삭제할 프로젝트를 먼저 열어주세요.")
            return
        reply = QMessageBox.question(
            self, "프로젝트 삭제",
            f"'{self._current_project.title}' 프로젝트를 삭제하시겠습니까?\n모든 챕터와 데이터가 삭제됩니다.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.db.delete_project(self._current_project.id)
            self._current_project = None
            self.setWindowTitle("NovelWriter Local")
            self.chapter_editor.set_project(None)
            self.character_panel.set_project(None)
            self.worldbuilding_panel.set_project(None)
            self._refresh_project_list()

    # ──────────────────────────────────────────
    # 내보내기 액션
    # ──────────────────────────────────────────

    def _export_chapter_txt(self):
        ch = self.chapter_editor._current_chapter
        if not ch:
            QMessageBox.information(self, "알림", "내보낼 챕터를 선택해주세요.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "챕터 txt 저장", f"{ch.chapter_num}화.txt", "텍스트 파일 (*.txt)")
        if path:
            from ..utils.export import export_chapter_txt
            export_chapter_txt(ch, path)
            self.status_bar.showMessage(f"내보내기 완료: {path}")

    def _export_all_txt(self):
        if not self._current_project:
            QMessageBox.information(self, "알림", "프로젝트를 먼저 열어주세요.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "전체 챕터 txt 저장",
                                               f"{self._current_project.title}.txt", "텍스트 파일 (*.txt)")
        if path:
            chapters = self.db.get_chapters_by_project(self._current_project.id)
            from ..utils.export import export_all_chapters_txt
            export_all_chapters_txt(self._current_project.title, chapters, path)
            self.status_bar.showMessage(f"내보내기 완료: {path}")

    def _export_docx(self):
        if not self._current_project:
            QMessageBox.information(self, "알림", "프로젝트를 먼저 열어주세요.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "전체 챕터 docx 저장",
                                               f"{self._current_project.title}.docx", "Word 문서 (*.docx)")
        if path:
            try:
                chapters = self.db.get_chapters_by_project(self._current_project.id)
                from ..utils.export import export_all_chapters_docx
                export_all_chapters_docx(self._current_project.title, chapters, path)
                self.status_bar.showMessage(f"내보내기 완료: {path}")
            except ImportError as e:
                QMessageBox.warning(self, "오류", str(e))

    # ──────────────────────────────────────────
    # 기타 액션
    # ──────────────────────────────────────────

    def _open_settings(self):
        dlg = SettingsDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._init_llm()
            self.status_bar.showMessage("설정이 저장되었습니다.")

    def _check_llm(self):
        if self._context_manager and self._context_manager.client.is_reachable():
            models = self._context_manager.client.list_models()
            model_str = ", ".join(models) if models else "목록 없음"
            QMessageBox.information(self, "LLM 연결", f"연결 성공!\n사용 가능한 모델: {model_str}")
        else:
            QMessageBox.warning(self, "LLM 연결", "LLM 서버에 연결할 수 없습니다.\n설정에서 엔드포인트를 확인해주세요.")

    def _on_chapter_saved(self):
        if self._context_manager and self.chapter_editor._current_chapter:
            # 백그라운드에서 요약 자동 생성 (선택적)
            pass

    def _show_about(self):
        QMessageBox.about(
            self, "NovelWriter Local 정보",
            "NovelWriter Local v1.0\n\n"
            "로컬 AI를 활용한 한국 웹소설 자동 생성 도구\n\n"
            "지원 LLM: Ollama, LM Studio\n"
            "추천 모델: Mistral, Llama 3, EEVE-Korean, Solar",
        )

    def closeEvent(self, event):
        """앱 종료 시 자동 저장"""
        if self.chapter_editor._modified and self.chapter_editor._current_chapter:
            reply = QMessageBox.question(
                self, "종료 확인",
                "저장되지 않은 변경사항이 있습니다. 저장하고 종료하시겠습니까?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
            )
            if reply == QMessageBox.StandardButton.Cancel:
                event.ignore()
                return
            if reply == QMessageBox.StandardButton.Yes:
                self.chapter_editor._save_current()
        self.db.close()
        event.accept()
