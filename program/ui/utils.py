"""UI 유틸리티 함수"""
from __future__ import annotations

from PySide6.QtWidgets import QGraphicsDropShadowEffect
from PySide6.QtGui import QColor

__all__ = ["create_shadow"]


def create_shadow(
    blur: int = 24,
    y_offset: int = 4,
    opacity: int = 20,
) -> QGraphicsDropShadowEffect:
    """그림자 효과 생성"""
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(blur)
    shadow.setXOffset(0)
    shadow.setYOffset(y_offset)
    shadow.setColor(QColor(0, 0, 0, opacity))
    return shadow
