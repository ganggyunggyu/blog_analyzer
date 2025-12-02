"""키워드 태그 칩 위젯"""
from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton

from program.ui.styles import COLORS

__all__ = ["KeywordChip"]


class KeywordChip(QFrame):
    """키워드 태그 칩"""

    removed = Signal(str)

    def __init__(self, keyword: str, parent=None):
        super().__init__(parent)
        self.keyword = keyword
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS["primary_soft"]};
                border-radius: 16px;
                padding: 0;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 8, 6)
        layout.setSpacing(6)

        label = QLabel(self.keyword)
        label.setStyleSheet(f"""
            color: {COLORS["primary"]};
            font-size: 13px;
            font-weight: 500;
            background: transparent;
        """)
        layout.addWidget(label)

        remove_btn = QPushButton("✕")
        remove_btn.setFixedSize(18, 18)
        remove_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                color: {COLORS["primary"]};
                font-size: 12px;
                font-weight: bold;
                padding: 0;
            }}
            QPushButton:hover {{
                color: {COLORS["error"]};
            }}
        """)
        remove_btn.clicked.connect(lambda: self.removed.emit(self.keyword))
        layout.addWidget(remove_btn)
