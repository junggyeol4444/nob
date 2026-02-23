"""세계관 관리 패널"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QFormLayout, QLineEdit, QTextEdit, QLabel,
    QDialog, QDialogButtonBox, QComboBox, QMessageBox,
)
from PyQt6.QtCore import Qt
from ..database.db_manager import DatabaseManager
from ..database.models import WorldBuilding


CATEGORIES = ["용어", "지명", "조직", "마법/능력", "아이템", "역사", "기타"]


class WorldBuildingEditDialog(QDialog):
    """세계관 항목 추가/편집 다이얼로그"""

    def __init__(self, parent=None, wb: WorldBuilding = None, project_id: int = None):
        super().__init__(parent)
        self.wb = wb
        self.project_id = project_id
        self._setup_ui()
        if wb:
            self._load(wb)

    def _setup_ui(self):
        is_edit = self.wb is not None
        self.setWindowTitle("세계관 편집" if is_edit else "세계관 항목 추가")
        self.setMinimumWidth(400)
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.category_combo = QComboBox()
        self.category_combo.addItems(CATEGORIES)
        self.category_combo.setEditable(True)
        form.addRow("분류", self.category_combo)

        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("항목 이름")
        form.addRow("이름 *", self.title_edit)

        self.content_edit = QTextEdit()
        self.content_edit.setPlaceholderText("상세 설명을 입력하세요")
        self.content_edit.setMinimumHeight(150)
        form.addRow("내용", self.content_edit)

        layout.addLayout(form)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load(self, wb: WorldBuilding):
        idx = self.category_combo.findText(wb.category)
        if idx >= 0:
            self.category_combo.setCurrentIndex(idx)
        else:
            self.category_combo.setCurrentText(wb.category)
        self.title_edit.setText(wb.title)
        self.content_edit.setPlainText(wb.content)

    def _accept(self):
        if not self.title_edit.text().strip():
            self.title_edit.setFocus()
            return
        self.accept()

    def get_worldbuilding(self) -> WorldBuilding:
        wb = self.wb or WorldBuilding(project_id=self.project_id)
        wb.category = self.category_combo.currentText().strip()
        wb.title = self.title_edit.text().strip()
        wb.content = self.content_edit.toPlainText().strip()
        return wb


class WorldBuildingPanel(QWidget):
    """세계관 관리 패널"""

    def __init__(self, db: DatabaseManager, project_id: int = None):
        super().__init__()
        self.db = db
        self.project_id = project_id
        self._setup_ui()
        if project_id:
            self.load_worldbuilding()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        layout.addWidget(QLabel("세계관 설정"))

        self.list_widget = QListWidget()
        self.list_widget.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self.list_widget)

        btn_row = QHBoxLayout()
        self.add_btn = QPushButton("추가")
        self.add_btn.clicked.connect(self._add_item)
        self.edit_btn = QPushButton("편집")
        self.edit_btn.clicked.connect(self._edit_item)
        self.edit_btn.setEnabled(False)
        self.del_btn = QPushButton("삭제")
        self.del_btn.clicked.connect(self._delete_item)
        self.del_btn.setEnabled(False)
        btn_row.addWidget(self.add_btn)
        btn_row.addWidget(self.edit_btn)
        btn_row.addWidget(self.del_btn)
        layout.addLayout(btn_row)

        self.content_label = QLabel()
        self.content_label.setWordWrap(True)
        self.content_label.setStyleSheet("color: #444; font-size: 11px; padding: 4px;")
        layout.addWidget(self.content_label)

    def set_project(self, project_id: int):
        self.project_id = project_id
        self.load_worldbuilding()

    def load_worldbuilding(self):
        self.list_widget.clear()
        self.content_label.clear()
        if not self.project_id:
            return
        items = self.db.get_worldbuilding_by_project(self.project_id)
        for wb in items:
            display = f"[{wb.category}] {wb.title}" if wb.category else wb.title
            item = QListWidgetItem(display)
            item.setData(Qt.ItemDataRole.UserRole, wb)
            self.list_widget.addItem(item)

    def _on_selection_changed(self):
        selected = self.list_widget.currentItem()
        has_sel = selected is not None
        self.edit_btn.setEnabled(has_sel)
        self.del_btn.setEnabled(has_sel)
        if selected:
            wb: WorldBuilding = selected.data(Qt.ItemDataRole.UserRole)
            self.content_label.setText(wb.content[:200])

    def _add_item(self):
        if not self.project_id:
            return
        dlg = WorldBuildingEditDialog(self, project_id=self.project_id)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            wb = dlg.get_worldbuilding()
            wb.id = self.db.create_worldbuilding(wb)
            self.load_worldbuilding()

    def _edit_item(self):
        item = self.list_widget.currentItem()
        if not item:
            return
        wb: WorldBuilding = item.data(Qt.ItemDataRole.UserRole)
        dlg = WorldBuildingEditDialog(self, wb=wb)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            updated = dlg.get_worldbuilding()
            self.db.update_worldbuilding(updated)
            self.load_worldbuilding()

    def _delete_item(self):
        item = self.list_widget.currentItem()
        if not item:
            return
        wb: WorldBuilding = item.data(Qt.ItemDataRole.UserRole)
        reply = QMessageBox.question(
            self, "삭제 확인",
            f"'{wb.title}' 항목을 삭제하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.db.delete_worldbuilding(wb.id)
            self.load_worldbuilding()
