"""UI 스타일 상수 정의"""
from __future__ import annotations

__all__ = ["COLORS", "STYLE_SHEET"]

COLORS = {
    "canvas": "#F5F7FA",
    "surface": "#FFFFFF",
    "primary": "#0064FF",
    "primary_soft": "#E0EDFF",
    "primary_hover": "#0055DD",
    "text_strong": "#111827",
    "text_muted": "#6B7280",
    "border": "#E5E7EB",
    "success": "#34C759",
    "error": "#FF3B30",
    "warning": "#FF9500",
}

STYLE_SHEET = f"""
QMainWindow {{
    background-color: {COLORS["canvas"]};
}}

QWidget {{
    background-color: transparent;
    color: {COLORS["text_strong"]};
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Pretendard", sans-serif;
    font-size: 14px;
}}

QLabel {{
    color: {COLORS["text_muted"]};
    font-size: 13px;
    background: transparent;
}}

QLabel#app_title {{
    color: {COLORS["text_strong"]};
    font-size: 22px;
    font-weight: 700;
}}

QLabel#app_subtitle {{
    color: {COLORS["text_muted"]};
    font-size: 13px;
}}

QLabel#section_title {{
    color: {COLORS["text_strong"]};
    font-size: 15px;
    font-weight: 600;
}}

QLabel#badge {{
    color: {COLORS["primary"]};
    background-color: {COLORS["primary_soft"]};
    font-size: 12px;
    font-weight: 600;
    padding: 6px 12px;
    border-radius: 14px;
}}

QLabel#char_count {{
    color: {COLORS["text_muted"]};
    font-size: 13px;
    font-weight: 500;
}}

QLineEdit {{
    background-color: {COLORS["surface"]};
    border: 1.5px solid {COLORS["border"]};
    border-radius: 12px;
    padding: 14px 16px;
    color: {COLORS["text_strong"]};
    font-size: 15px;
}}

QLineEdit:focus {{
    border: 2px solid {COLORS["primary"]};
    padding: 13px 15px;
}}

QTextEdit {{
    background-color: {COLORS["surface"]};
    border: 1.5px solid {COLORS["border"]};
    border-radius: 12px;
    padding: 14px;
    color: {COLORS["text_strong"]};
    font-size: 14px;
    line-height: 1.7;
}}

QTextEdit:focus {{
    border: 2px solid {COLORS["primary"]};
}}

QComboBox {{
    background-color: {COLORS["surface"]};
    border: 1.5px solid {COLORS["border"]};
    border-radius: 12px;
    padding: 14px 16px;
    color: {COLORS["text_strong"]};
    font-size: 15px;
    min-width: 180px;
}}

QComboBox:hover, QComboBox:focus {{
    border: 2px solid {COLORS["primary"]};
}}

QComboBox::drop-down {{
    border: none;
    padding-right: 12px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {COLORS["text_muted"]};
}}

QComboBox QAbstractItemView {{
    background-color: {COLORS["surface"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 8px;
    padding: 6px;
    selection-background-color: {COLORS["primary_soft"]};
    selection-color: {COLORS["primary"]};
}}

QPushButton#secondary {{
    background-color: {COLORS["surface"]};
    border: 1.5px solid {COLORS["border"]};
    border-radius: 10px;
    padding: 10px 20px;
    color: {COLORS["text_strong"]};
    font-size: 14px;
    font-weight: 500;
}}

QPushButton#secondary:hover {{
    background-color: {COLORS["canvas"]};
    border-color: {COLORS["primary"]};
}}

QPushButton#ghost {{
    background-color: transparent;
    border: none;
    color: {COLORS["primary"]};
    font-size: 13px;
    font-weight: 500;
    padding: 8px 12px;
}}

QPushButton#ghost:hover {{
    background-color: {COLORS["primary_soft"]};
    border-radius: 8px;
}}

QPushButton#toggle {{
    background-color: transparent;
    border: none;
    color: {COLORS["text_muted"]};
    font-size: 13px;
    padding: 8px 0;
    text-align: left;
}}

QPushButton#toggle:hover {{
    color: {COLORS["primary"]};
}}

QListWidget {{
    background-color: transparent;
    border: none;
    outline: none;
}}

QListWidget::item {{
    background-color: {COLORS["surface"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 12px;
    padding: 14px 16px;
    margin-bottom: 8px;
    color: {COLORS["text_strong"]};
}}

QListWidget::item:selected {{
    background-color: {COLORS["primary_soft"]};
    border-color: {COLORS["primary"]};
}}

QListWidget::item:hover {{
    border-color: {COLORS["primary"]};
}}

QStatusBar {{
    background-color: {COLORS["surface"]};
    border-top: 1px solid {COLORS["border"]};
    color: {COLORS["text_muted"]};
    font-size: 12px;
}}

QProgressBar {{
    background-color: {COLORS["border"]};
    border: none;
    border-radius: 3px;
    height: 6px;
}}

QProgressBar::chunk {{
    background-color: {COLORS["primary"]};
    border-radius: 3px;
}}

QScrollBar:vertical {{
    background: transparent;
    width: 8px;
}}

QScrollBar::handle:vertical {{
    background: {COLORS["border"]};
    border-radius: 4px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background: {COLORS["text_muted"]};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: none;
    height: 0;
}}

QScrollBar:horizontal {{
    height: 0;
    background: transparent;
}}

QFrame#card {{
    background-color: {COLORS["surface"]};
    border-radius: 16px;
}}

QFrame#sidebar {{
    background-color: {COLORS["surface"]};
}}
"""
