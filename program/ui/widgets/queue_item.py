"""생성 큐 아이템 위젯"""
from __future__ import annotations

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel

from program.ui.styles import COLORS

__all__ = ["QueueItem"]


class QueueItem(QFrame):
    """생성 큐 아이템"""

    def __init__(self, keyword: str, index: int, parent=None):
        super().__init__(parent)
        self.keyword = keyword
        self.index = index
        self.status = "pending"
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS["surface"]};
                border: 1px solid {COLORS["border"]};
                border-radius: 10px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(10)

        self.status_label = QLabel("○")
        self.status_label.setFixedWidth(20)
        self.status_label.setStyleSheet(
            f"color: {COLORS['text_muted']}; font-size: 14px;"
        )
        layout.addWidget(self.status_label)

        self.keyword_label = QLabel(self.keyword)
        self.keyword_label.setStyleSheet(
            f"color: {COLORS['text_strong']}; font-size: 14px;"
        )
        layout.addWidget(self.keyword_label, stretch=1)

        self.info_label = QLabel("대기")
        self.info_label.setStyleSheet(
            f"color: {COLORS['text_muted']}; font-size: 12px;"
        )
        layout.addWidget(self.info_label)

    def set_status(self, status: str, info: str = "") -> None:
        """상태 업데이트"""
        self.status = status

        status_config = {
            "pending": ("○", COLORS["text_muted"], "대기", COLORS["text_muted"]),
            "running": ("◐", COLORS["warning"], "생성 중...", COLORS["warning"]),
            "done": ("✓", COLORS["success"], info or "완료", COLORS["success"]),
            "error": ("✕", COLORS["error"], "실패", COLORS["error"]),
        }

        if status in status_config:
            icon, icon_color, text, text_color = status_config[status]
            self.status_label.setText(icon)
            self.status_label.setStyleSheet(f"color: {icon_color}; font-size: 14px;")
            self.info_label.setText(text)
            self.info_label.setStyleSheet(f"color: {text_color}; font-size: 12px;")
