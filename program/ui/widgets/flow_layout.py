"""플로우 레이아웃"""
from __future__ import annotations

from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget

__all__ = ["FlowLayout"]


class FlowLayout(QVBoxLayout):
    """간단한 FlowLayout 구현 (가로로 칩 배치)"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items: list[QWidget] = []
        self._row_layout: QHBoxLayout | None = None
        self._init_row()

    def _init_row(self) -> None:
        self._row_layout = QHBoxLayout()
        self._row_layout.setSpacing(8)
        self._row_layout.setContentsMargins(0, 0, 0, 0)
        self._row_layout.addStretch()
        super().addLayout(self._row_layout)

    def addWidget(self, widget: QWidget) -> None:
        """위젯 추가"""
        self._items.append(widget)
        self._row_layout.insertWidget(self._row_layout.count() - 1, widget)

    def removeWidget(self, widget: QWidget) -> None:
        """위젯 제거"""
        if widget in self._items:
            self._items.remove(widget)
        self._row_layout.removeWidget(widget)
