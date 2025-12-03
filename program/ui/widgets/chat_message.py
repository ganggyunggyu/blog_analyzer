"""채팅 메시지 위젯"""
from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel

from program.ui.styles import COLORS

__all__ = ["ChatMessage"]


class ChatMessage(QFrame):
    """Hoverable Card 스타일 채팅 메시지 (클릭 이벤트 지원)"""

    clicked = Signal(str)  # content 전달

    def __init__(
        self,
        content: str,
        sender: str = "user",
        parent=None,
    ):
        super().__init__(parent)
        self.content = content
        self.sender = sender  # "user" or "ai"
        self._setup_ui()
        self.setCursor("PointingHandCursor")

    def _setup_ui(self) -> None:
        # 유저: 파란색 배경 / AI: 흰색 배경
        if self.sender == "user":
            self._bg_color = COLORS["primary_soft"]
            self._hover_color = "#D0E3FF"  # 조금 더 진한 파랑
            self._text_color = COLORS["primary"]
        else:
            self._bg_color = COLORS["surface"]
            self._hover_color = COLORS["canvas"]  # 연한 회색
            self._text_color = COLORS["text_strong"]

        self._apply_style(self._bg_color)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(6)

        # 발신자 라벨
        sender_label = QLabel("나" if self.sender == "user" else "AI")
        sender_label.setStyleSheet(f"""
            color: {COLORS["text_muted"]};
            font-size: 12px;
            font-weight: 600;
            background: transparent;
            border: none;
        """)
        layout.addWidget(sender_label)

        # 메시지 내용
        self.content_label = QLabel(self.content)
        self.content_label.setWordWrap(True)
        self.content_label.setStyleSheet(f"""
            color: {self._text_color};
            font-size: 14px;
            line-height: 1.5;
            background: transparent;
            border: none;
        """)
        layout.addWidget(self.content_label)

    def _apply_style(self, bg_color: str) -> None:
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: 1px solid {COLORS["border"]};
                border-radius: 16px;
            }}
        """)

    def enterEvent(self, event) -> None:
        """마우스 호버 진입"""
        self._apply_style(self._hover_color)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        """마우스 호버 이탈"""
        self._apply_style(self._bg_color)
        super().leaveEvent(event)

    def mousePressEvent(self, event) -> None:
        """클릭 이벤트"""
        self.clicked.emit(self.content)
        super().mousePressEvent(event)

    def set_content(self, content: str) -> None:
        """내용 업데이트"""
        self.content = content
        self.content_label.setText(content)

    @staticmethod
    def create_user_message(content: str, parent=None) -> "ChatMessage":
        """유저 메시지 생성 헬퍼"""
        return ChatMessage(content, sender="user", parent=parent)

    @staticmethod
    def create_ai_message(content: str, parent=None) -> "ChatMessage":
        """AI 메시지 생성 헬퍼"""
        return ChatMessage(content, sender="ai", parent=parent)
