"""프로젝트 생성/편집 다이얼로그"""
from PyQt6.QtWidgets import (
    QDialog, QDialogButtonBox, QFormLayout, QLineEdit,
    QTextEdit, QComboBox, QVBoxLayout, QLabel,
)
from ..database.models import Project


GENRES = ["판타지", "로맨스", "무협", "현대물", "SF", "공포", "미스터리", "역사", "기타"]
TONES = [
    "1인칭 주인공 시점",
    "3인칭 관찰자 시점",
    "3인칭 전지적 작가 시점",
    "2인칭",
]


class ProjectDialog(QDialog):
    """프로젝트 생성/편집 다이얼로그"""

    def __init__(self, parent=None, project: Project = None):
        super().__init__(parent)
        self.project = project
        self._setup_ui()
        if project:
            self._load_project(project)

    def _setup_ui(self):
        is_edit = self.project is not None
        self.setWindowTitle("프로젝트 편집" if is_edit else "새 프로젝트")
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("작품 제목을 입력하세요")
        form.addRow("제목 *", self.title_edit)

        self.genre_combo = QComboBox()
        self.genre_combo.addItems(GENRES)
        form.addRow("장르", self.genre_combo)

        self.tone_combo = QComboBox()
        self.tone_combo.addItems(TONES)
        form.addRow("시점/톤", self.tone_combo)

        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("작품 소개 (선택)")
        self.description_edit.setMaximumHeight(80)
        form.addRow("소개", self.description_edit)

        self.plot_edit = QTextEdit()
        self.plot_edit.setPlaceholderText("기본 플롯 / 줄거리 개요를 입력하세요")
        self.plot_edit.setMinimumHeight(120)
        form.addRow("플롯", self.plot_edit)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_project(self, project: Project):
        self.title_edit.setText(project.title)
        idx = self.genre_combo.findText(project.genre)
        if idx >= 0:
            self.genre_combo.setCurrentIndex(idx)
        idx = self.tone_combo.findText(project.tone)
        if idx >= 0:
            self.tone_combo.setCurrentIndex(idx)
        self.description_edit.setPlainText(project.description)
        self.plot_edit.setPlainText(project.plot)

    def _accept(self):
        title = self.title_edit.text().strip()
        if not title:
            self.title_edit.setFocus()
            self.title_edit.setStyleSheet("border: 1px solid red;")
            return
        self.title_edit.setStyleSheet("")
        self.accept()

    def get_project_data(self) -> Project:
        """입력된 데이터로 Project 객체 반환"""
        p = self.project or Project()
        p.title = self.title_edit.text().strip()
        p.genre = self.genre_combo.currentText()
        p.tone = self.tone_combo.currentText()
        p.description = self.description_edit.toPlainText().strip()
        p.plot = self.plot_edit.toPlainText().strip()
        return p
