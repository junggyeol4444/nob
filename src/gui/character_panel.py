"""캐릭터 관리 패널"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QFormLayout, QLineEdit, QSpinBox, QTextEdit,
    QLabel, QSplitter, QMessageBox, QDialog, QDialogButtonBox,
)
from PyQt6.QtCore import Qt
from ..database.db_manager import DatabaseManager
from ..database.models import Character


class CharacterEditDialog(QDialog):
    """캐릭터 추가/편집 다이얼로그"""

    def __init__(self, parent=None, character: Character = None, project_id: int = None):
        super().__init__(parent)
        self.character = character
        self.project_id = project_id
        self._setup_ui()
        if character:
            self._load(character)

    def _setup_ui(self):
        is_edit = self.character is not None
        self.setWindowTitle("캐릭터 편집" if is_edit else "캐릭터 추가")
        self.setMinimumWidth(420)
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("이름을 입력하세요")
        form.addRow("이름 *", self.name_edit)

        self.age_spin = QSpinBox()
        self.age_spin.setRange(0, 999)
        self.age_spin.setSpecialValueText("미설정")
        form.addRow("나이", self.age_spin)

        self.personality_edit = QTextEdit()
        self.personality_edit.setMaximumHeight(70)
        self.personality_edit.setPlaceholderText("성격, 말투 등")
        form.addRow("성격", self.personality_edit)

        self.appearance_edit = QTextEdit()
        self.appearance_edit.setMaximumHeight(70)
        self.appearance_edit.setPlaceholderText("외모 묘사")
        form.addRow("외모", self.appearance_edit)

        self.background_edit = QTextEdit()
        self.background_edit.setMaximumHeight(70)
        self.background_edit.setPlaceholderText("배경, 과거 이력")
        form.addRow("배경", self.background_edit)

        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(70)
        self.notes_edit.setPlaceholderText("메모 (자유 형식)")
        form.addRow("메모", self.notes_edit)

        layout.addLayout(form)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load(self, c: Character):
        self.name_edit.setText(c.name)
        self.age_spin.setValue(c.age or 0)
        self.personality_edit.setPlainText(c.personality)
        self.appearance_edit.setPlainText(c.appearance)
        self.background_edit.setPlainText(c.background)
        self.notes_edit.setPlainText(c.notes)

    def _accept(self):
        if not self.name_edit.text().strip():
            self.name_edit.setFocus()
            return
        self.accept()

    def get_character(self) -> Character:
        c = self.character or Character(project_id=self.project_id)
        c.name = self.name_edit.text().strip()
        age = self.age_spin.value()
        c.age = age if age > 0 else None
        c.personality = self.personality_edit.toPlainText().strip()
        c.appearance = self.appearance_edit.toPlainText().strip()
        c.background = self.background_edit.toPlainText().strip()
        c.notes = self.notes_edit.toPlainText().strip()
        return c


class CharacterPanel(QWidget):
    """캐릭터 관리 패널 (오른쪽 패널 탭)"""

    def __init__(self, db: DatabaseManager, project_id: int = None):
        super().__init__()
        self.db = db
        self.project_id = project_id
        self._setup_ui()
        if project_id:
            self.load_characters()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        layout.addWidget(QLabel("캐릭터 목록"))

        self.list_widget = QListWidget()
        self.list_widget.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self.list_widget)

        btn_row = QHBoxLayout()
        self.add_btn = QPushButton("추가")
        self.add_btn.clicked.connect(self._add_character)
        self.edit_btn = QPushButton("편집")
        self.edit_btn.clicked.connect(self._edit_character)
        self.edit_btn.setEnabled(False)
        self.del_btn = QPushButton("삭제")
        self.del_btn.clicked.connect(self._delete_character)
        self.del_btn.setEnabled(False)
        btn_row.addWidget(self.add_btn)
        btn_row.addWidget(self.edit_btn)
        btn_row.addWidget(self.del_btn)
        layout.addLayout(btn_row)

        # 간단한 정보 표시 영역
        self.info_label = QLabel()
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("color: #555; font-size: 11px; padding: 4px;")
        layout.addWidget(self.info_label)

    def set_project(self, project_id: int):
        self.project_id = project_id
        self.load_characters()

    def load_characters(self):
        self.list_widget.clear()
        self.info_label.clear()
        if not self.project_id:
            return
        characters = self.db.get_characters_by_project(self.project_id)
        for c in characters:
            item = QListWidgetItem(c.name)
            item.setData(Qt.ItemDataRole.UserRole, c)
            self.list_widget.addItem(item)

    def _on_selection_changed(self):
        selected = self.list_widget.currentItem()
        has_sel = selected is not None
        self.edit_btn.setEnabled(has_sel)
        self.del_btn.setEnabled(has_sel)
        if selected:
            c: Character = selected.data(Qt.ItemDataRole.UserRole)
            info_parts = []
            if c.age:
                info_parts.append(f"나이: {c.age}세")
            if c.personality:
                info_parts.append(f"성격: {c.personality[:50]}")
            if c.appearance:
                info_parts.append(f"외모: {c.appearance[:50]}")
            self.info_label.setText("\n".join(info_parts))

    def _add_character(self):
        if not self.project_id:
            return
        dlg = CharacterEditDialog(self, project_id=self.project_id)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            char = dlg.get_character()
            char.id = self.db.create_character(char)
            self.load_characters()

    def _edit_character(self):
        item = self.list_widget.currentItem()
        if not item:
            return
        c: Character = item.data(Qt.ItemDataRole.UserRole)
        dlg = CharacterEditDialog(self, character=c)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            updated = dlg.get_character()
            self.db.update_character(updated)
            self.load_characters()

    def _delete_character(self):
        item = self.list_widget.currentItem()
        if not item:
            return
        c: Character = item.data(Qt.ItemDataRole.UserRole)
        reply = QMessageBox.question(
            self, "삭제 확인",
            f"'{c.name}' 캐릭터를 삭제하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.db.delete_character(c.id)
            self.load_characters()
