"""챕터 편집기 위젯"""
import threading
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QTextEdit, QLabel, QLineEdit, QSplitter,
    QMessageBox, QInputDialog, QDialog, QSizePolicy,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from ..database.db_manager import DatabaseManager
from ..database.models import Chapter


class ChapterEditor(QWidget):
    """챕터 목록 + 텍스트 편집기 위젯"""

    chapter_saved = pyqtSignal()

    def __init__(self, db: DatabaseManager, project_id: int = None):
        super().__init__()
        self.db = db
        self.project_id = project_id
        self._current_chapter: Chapter = None
        self._modified = False
        self._context_manager = None

        self._setup_ui()
        self._setup_auto_save()

        if project_id:
            self.load_chapters()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # ── 왼쪽: 챕터 목록 ──
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(4, 4, 4, 4)

        left_layout.addWidget(QLabel("챕터 목록"))
        self.chapter_list = QListWidget()
        self.chapter_list.currentItemChanged.connect(self._on_chapter_selected)
        left_layout.addWidget(self.chapter_list)

        ch_btn_row = QHBoxLayout()
        self.add_ch_btn = QPushButton("+ 챕터")
        self.add_ch_btn.clicked.connect(self._add_chapter)
        self.del_ch_btn = QPushButton("삭제")
        self.del_ch_btn.clicked.connect(self._delete_chapter)
        self.del_ch_btn.setEnabled(False)
        ch_btn_row.addWidget(self.add_ch_btn)
        ch_btn_row.addWidget(self.del_ch_btn)
        left_layout.addLayout(ch_btn_row)

        left_widget.setMaximumWidth(220)
        splitter.addWidget(left_widget)

        # ── 오른쪽: 편집기 ──
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(4, 4, 4, 4)

        # 챕터 제목 입력
        title_row = QHBoxLayout()
        title_row.addWidget(QLabel("제목:"))
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("챕터 제목 (선택)")
        self.title_edit.textChanged.connect(self._mark_modified)
        title_row.addWidget(self.title_edit)
        right_layout.addLayout(title_row)

        # 본문 편집기
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("챕터 내용을 입력하세요...")
        self.text_edit.textChanged.connect(self._mark_modified)
        right_layout.addWidget(self.text_edit)

        # 하단 상태바 및 버튼
        bottom_row = QHBoxLayout()
        self.word_count_label = QLabel("0자")
        self.word_count_label.setStyleSheet("color: #666;")
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #888; font-size: 11px;")

        self.save_btn = QPushButton("저장 (Ctrl+S)")
        self.save_btn.clicked.connect(self._save_current)
        self.save_btn.setEnabled(False)

        self.ai_gen_btn = QPushButton("✨ AI 생성")
        self.ai_gen_btn.clicked.connect(self._open_generation_dialog)
        self.ai_gen_btn.setEnabled(False)

        self.history_btn = QPushButton("히스토리")
        self.history_btn.clicked.connect(self._show_history)
        self.history_btn.setEnabled(False)

        bottom_row.addWidget(self.word_count_label)
        bottom_row.addWidget(self.status_label)
        bottom_row.addStretch()
        bottom_row.addWidget(self.history_btn)
        bottom_row.addWidget(self.ai_gen_btn)
        bottom_row.addWidget(self.save_btn)
        right_layout.addLayout(bottom_row)

        splitter.addWidget(right_widget)
        splitter.setStretchFactor(1, 3)
        layout.addWidget(splitter)

        # 단축키
        from PyQt6.QtGui import QKeySequence, QShortcut
        save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        save_shortcut.activated.connect(self._save_current)

        self.text_edit.textChanged.connect(self._update_word_count)

    def _setup_auto_save(self):
        """설정에서 읽은 자동 저장 주기로 타이머 설정"""
        from ..utils import config
        interval_sec = config.get("auto_save_interval", 30)
        self._auto_save_timer = QTimer(self)
        self._auto_save_timer.timeout.connect(self._auto_save)
        self._auto_save_timer.start(interval_sec * 1000)

    def set_project(self, project_id: int):
        self.project_id = project_id
        self._current_chapter = None
        self.load_chapters()

    def set_context_manager(self, context_manager):
        self._context_manager = context_manager
        self.ai_gen_btn.setEnabled(self._current_chapter is not None)

    def load_chapters(self):
        self.chapter_list.clear()
        if not self.project_id:
            return
        chapters = self.db.get_chapters_by_project(self.project_id)
        for ch in chapters:
            label = f"{ch.chapter_num}화" + (f": {ch.title}" if ch.title else "")
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, ch)
            self.chapter_list.addItem(item)

    def _on_chapter_selected(self, current, previous):
        if self._modified and self._current_chapter:
            reply = QMessageBox.question(
                self, "저장 확인",
                "변경된 내용이 있습니다. 저장하시겠습니까?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
            )
            if reply == QMessageBox.StandardButton.Cancel:
                self.chapter_list.setCurrentItem(previous)
                return
            if reply == QMessageBox.StandardButton.Yes:
                self._save_current()

        if current is None:
            self._current_chapter = None
            self._set_editor_enabled(False)
            return

        ch: Chapter = current.data(Qt.ItemDataRole.UserRole)
        # DB에서 최신 데이터 가져오기
        self._current_chapter = self.db.get_chapter(ch.id)
        self._load_chapter(self._current_chapter)

    def _load_chapter(self, chapter: Chapter):
        self._modified = False
        self.title_edit.blockSignals(True)
        self.text_edit.blockSignals(True)
        self.title_edit.setText(chapter.title or "")
        self.text_edit.setPlainText(chapter.content or "")
        self.title_edit.blockSignals(False)
        self.text_edit.blockSignals(False)
        self._set_editor_enabled(True)
        self._update_word_count()
        self.status_label.setText("")

    def _set_editor_enabled(self, enabled: bool):
        self.title_edit.setEnabled(enabled)
        self.text_edit.setEnabled(enabled)
        self.save_btn.setEnabled(enabled)
        self.del_ch_btn.setEnabled(enabled)
        self.history_btn.setEnabled(enabled)
        self.ai_gen_btn.setEnabled(enabled and self._context_manager is not None)

    def _mark_modified(self):
        self._modified = True
        self.status_label.setText("● 수정됨")

    def _update_word_count(self):
        text = self.text_edit.toPlainText()
        count = len(text.replace(" ", "").replace("\n", ""))
        self.word_count_label.setText(f"{count:,}자")

    def _save_current(self):
        if not self._current_chapter:
            return
        content = self.text_edit.toPlainText()
        self._current_chapter.title = self.title_edit.text().strip()
        self._current_chapter.content = content
        self._current_chapter.word_count = len(content.replace(" ", "").replace("\n", ""))
        self.db.update_chapter(self._current_chapter)
        self._modified = False
        self.status_label.setText("✓ 저장됨")
        self.chapter_saved.emit()

        # 챕터 목록 라벨 갱신
        item = self.chapter_list.currentItem()
        if item:
            ch = self._current_chapter
            label = f"{ch.chapter_num}화" + (f": {ch.title}" if ch.title else "")
            item.setText(label)

    def _auto_save(self):
        if self._modified and self._current_chapter:
            self._save_current()

    def _add_chapter(self):
        if not self.project_id:
            return
        if self._modified and self._current_chapter:
            self._save_current()
        next_num = self.db.get_next_chapter_num(self.project_id)
        chapter = Chapter(
            project_id=self.project_id,
            chapter_num=next_num,
            title="",
            content="",
        )
        chapter.id = self.db.create_chapter(chapter)
        self.load_chapters()
        # 방금 추가한 챕터 선택
        for i in range(self.chapter_list.count()):
            item = self.chapter_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole).id == chapter.id:
                self.chapter_list.setCurrentItem(item)
                break

    def _delete_chapter(self):
        item = self.chapter_list.currentItem()
        if not item:
            return
        ch: Chapter = item.data(Qt.ItemDataRole.UserRole)
        reply = QMessageBox.question(
            self, "삭제 확인",
            f"{ch.chapter_num}화를 삭제하시겠습니까? (복구 불가)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.db.delete_chapter(ch.id)
            self._current_chapter = None
            self._modified = False
            self.load_chapters()
            self._set_editor_enabled(False)
            self.title_edit.clear()
            self.text_edit.clear()

    def _open_generation_dialog(self):
        if not self._context_manager or not self._current_chapter:
            return
        from .generation_dialog import GenerationDialog
        dlg = GenerationDialog(self, self._context_manager, self.project_id)
        dlg.generation_complete.connect(self._on_generation_complete)
        dlg.exec()

    def _on_generation_complete(self, text: str):
        """AI 생성 완료 - 현재 챕터에 삽입"""
        if not self._current_chapter:
            return
        # 생성 이력 저장 (현재 내용)
        if self._current_chapter.content:
            self.db.save_generation_history(self._current_chapter.id, self._current_chapter.content)
        # 생성된 내용 설정
        self.text_edit.setPlainText(text)
        self._save_current()

    def _show_history(self):
        if not self._current_chapter:
            return
        histories = self.db.get_generation_history(self._current_chapter.id)
        if not histories:
            QMessageBox.information(self, "히스토리", "저장된 생성 히스토리가 없습니다.")
            return
        self._show_history_dialog(histories)

    def _show_history_dialog(self, histories):
        from PyQt6.QtWidgets import QDialog, QListWidget, QTextEdit, QDialogButtonBox
        dlg = QDialog(self)
        dlg.setWindowTitle("생성 히스토리")
        dlg.setMinimumSize(700, 500)
        layout = QVBoxLayout(dlg)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        list_w = QListWidget()
        for h in histories:
            item = QListWidgetItem(f"v{h.version} ({h.created_at or ''})")
            item.setData(Qt.ItemDataRole.UserRole, h)
            list_w.addItem(item)
        splitter.addWidget(list_w)

        preview = QTextEdit()
        preview.setReadOnly(True)
        splitter.addWidget(preview)

        def on_select(current, _):
            if current:
                h = current.data(Qt.ItemDataRole.UserRole)
                preview.setPlainText(h.content)

        list_w.currentItemChanged.connect(on_select)
        layout.addWidget(splitter)

        btn_row = QHBoxLayout()
        rollback_btn = QPushButton("이 버전으로 롤백")

        def rollback():
            item = list_w.currentItem()
            if item:
                h = item.data(Qt.ItemDataRole.UserRole)
                self.text_edit.setPlainText(h.content)
                self._mark_modified()
                dlg.accept()

        rollback_btn.clicked.connect(rollback)
        close_btn = QPushButton("닫기")
        close_btn.clicked.connect(dlg.reject)
        btn_row.addWidget(rollback_btn)
        btn_row.addStretch()
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

        dlg.exec()
