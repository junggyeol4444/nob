"""AI 챕터 생성 다이얼로그"""
import threading
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QTextEdit, QCheckBox, QPushButton, QProgressBar, QMessageBox,
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject


WORD_COUNT_OPTIONS = [1000, 2000, 3000, 5000]


class _Worker(QObject):
    """백그라운드 LLM 생성 워커"""
    token_received = pyqtSignal(str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, context_manager, project_id, user_request, target_length,
                 include_context, include_characters):
        super().__init__()
        self.context_manager = context_manager
        self.project_id = project_id
        self.user_request = user_request
        self.target_length = target_length
        self.include_context = include_context
        self.include_characters = include_characters
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        try:
            result = self.context_manager.generate_chapter(
                project_id=self.project_id,
                user_request=self.user_request,
                target_length=self.target_length,
                include_context=self.include_context,
                include_characters=self.include_characters,
                on_token=self._on_token,
            )
            if not self._cancelled:
                self.finished.emit(result)
        except Exception as e:
            if not self._cancelled:
                self.error.emit(str(e))

    def _on_token(self, token: str):
        if not self._cancelled:
            self.token_received.emit(token)


class GenerationDialog(QDialog):
    """AI 챕터 자동 생성 다이얼로그"""

    generation_complete = pyqtSignal(str)  # 생성 완료 시 결과 텍스트 전달

    def __init__(self, parent, context_manager, project_id: int):
        super().__init__(parent)
        self.context_manager = context_manager
        self.project_id = project_id
        self._worker = None
        self._thread = None
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("AI 챕터 생성")
        self.setMinimumSize(500, 400)
        layout = QVBoxLayout(self)

        # 분량 선택
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("분량:"))
        self.count_combo = QComboBox()
        for n in WORD_COUNT_OPTIONS:
            self.count_combo.addItem(f"{n:,}자", n)
        self.count_combo.setCurrentIndex(1)  # 기본 2000자
        row1.addWidget(self.count_combo)
        row1.addStretch()
        layout.addLayout(row1)

        # 요청사항 입력
        layout.addWidget(QLabel("요청사항 (다음 챕터에 포함할 내용):"))
        self.request_edit = QTextEdit()
        self.request_edit.setPlaceholderText(
            "예: 주인공이 적과 처음 만나는 장면을 긴장감 있게 작성해주세요."
        )
        self.request_edit.setMaximumHeight(100)
        layout.addWidget(self.request_edit)

        # 옵션 체크박스
        self.ctx_check = QCheckBox("이전 챕터 맥락 포함")
        self.ctx_check.setChecked(True)
        self.char_check = QCheckBox("캐릭터 정보 참조")
        self.char_check.setChecked(True)
        layout.addWidget(self.ctx_check)
        layout.addWidget(self.char_check)

        # 프리뷰 영역
        layout.addWidget(QLabel("생성 미리보기:"))
        self.preview_edit = QTextEdit()
        self.preview_edit.setReadOnly(True)
        self.preview_edit.setPlaceholderText("여기에 생성된 내용이 표시됩니다...")
        layout.addWidget(self.preview_edit)

        # 진행 표시
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # 무한 루프
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # 버튼
        btn_row = QHBoxLayout()
        self.generate_btn = QPushButton("생성")
        self.generate_btn.setDefault(True)
        self.generate_btn.clicked.connect(self._start_generation)

        self.cancel_btn = QPushButton("취소")
        self.cancel_btn.clicked.connect(self._cancel_or_close)

        self.apply_btn = QPushButton("적용")
        self.apply_btn.setEnabled(False)
        self.apply_btn.clicked.connect(self._apply)

        btn_row.addWidget(self.generate_btn)
        btn_row.addWidget(self.cancel_btn)
        btn_row.addStretch()
        btn_row.addWidget(self.apply_btn)
        layout.addLayout(btn_row)

    def _start_generation(self):
        self.preview_edit.clear()
        self.generate_btn.setEnabled(False)
        self.apply_btn.setEnabled(False)
        self.progress_bar.setVisible(True)

        target_length = self.count_combo.currentData()
        user_request = self.request_edit.toPlainText().strip()

        self._worker = _Worker(
            context_manager=self.context_manager,
            project_id=self.project_id,
            user_request=user_request,
            target_length=target_length,
            include_context=self.ctx_check.isChecked(),
            include_characters=self.char_check.isChecked(),
        )
        self._worker.token_received.connect(self._on_token)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)

        self._thread = threading.Thread(target=self._worker.run, daemon=True)
        self._thread.start()

    def _on_token(self, token: str):
        cursor = self.preview_edit.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText(token)
        self.preview_edit.setTextCursor(cursor)
        self.preview_edit.ensureCursorVisible()

    def _on_finished(self, result: str):
        self.progress_bar.setVisible(False)
        self.generate_btn.setEnabled(True)
        self.apply_btn.setEnabled(True)
        self._generated_text = result

    def _on_error(self, message: str):
        self.progress_bar.setVisible(False)
        self.generate_btn.setEnabled(True)
        QMessageBox.critical(self, "생성 오류", f"AI 생성 중 오류가 발생했습니다:\n{message}")

    def _cancel_or_close(self):
        if self._worker:
            self._worker.cancel()
        self.reject()

    def _apply(self):
        text = self.preview_edit.toPlainText()
        if text:
            self.generation_complete.emit(text)
        self.accept()

    def closeEvent(self, event):
        if self._worker:
            self._worker.cancel()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
        super().closeEvent(event)
