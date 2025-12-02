"""메인 윈도우"""
from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QComboBox,
    QPushButton,
    QStatusBar,
    QProgressBar,
    QListWidget,
    QListWidgetItem,
    QFrame,
    QSizePolicy,
    QScrollArea,
    QApplication,
)

from program.core import Generator
from program.ui.styles import COLORS, STYLE_SHEET
from program.ui.workers import BatchGenerateWorker
from program.ui.models import HistoryItem
from program.ui.utils import create_shadow
from program.ui.widgets import KeywordChip, QueueItem, FlowLayout

__all__ = ["MainWindow"]


class MainWindow(QMainWindow):
    """메인 윈도우"""

    def __init__(self):
        super().__init__()
        self.worker: BatchGenerateWorker | None = None
        self.history: list[HistoryItem] = []
        self.keywords: list[str] = []
        self.keyword_chips: dict[str, KeywordChip] = {}
        self.queue_items: list[QueueItem] = []
        self.results: dict[int, tuple[str, str]] = {}
        self.ref_expanded = False
        self.is_generating = False
        self._setup_ui()
        self._load_history_from_db()

    def _setup_ui(self) -> None:
        self.setWindowTitle("Blog Analyzer")
        self.setMinimumSize(1200, 750)
        self.setStyleSheet(STYLE_SHEET)

        central = QWidget()
        central.setStyleSheet(f"background-color: {COLORS['canvas']};")
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self._setup_sidebar(main_layout)
        self._setup_content(main_layout)
        self._setup_status_bar()

    def _setup_sidebar(self, main_layout: QHBoxLayout) -> None:
        """좌측 사이드바 설정"""
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(300)
        sidebar.setStyleSheet(f"""
            QFrame#sidebar {{
                background-color: {COLORS["surface"]};
                border-right: 1px solid {COLORS["border"]};
            }}
        """)

        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(20, 28, 20, 20)
        sidebar_layout.setSpacing(20)

        # 앱 타이틀
        title_section = QVBoxLayout()
        title_section.setSpacing(2)

        app_title = QLabel("Blog Analyzer")
        app_title.setObjectName("app_title")
        title_section.addWidget(app_title)

        app_subtitle = QLabel("AI 블로그 원고 생성기")
        app_subtitle.setObjectName("app_subtitle")
        title_section.addWidget(app_subtitle)

        sidebar_layout.addLayout(title_section)

        # 히스토리 헤더
        history_header = QHBoxLayout()
        history_title = QLabel("최근 작업")
        history_title.setObjectName("section_title")
        history_header.addWidget(history_title)
        history_header.addStretch()

        self.refresh_btn = QPushButton("새로고침")
        self.refresh_btn.setObjectName("ghost")
        self.refresh_btn.clicked.connect(self._load_history_from_db)
        history_header.addWidget(self.refresh_btn)

        sidebar_layout.addLayout(history_header)

        # 히스토리 리스트
        self.history_list = QListWidget()
        self.history_list.itemClicked.connect(self._on_history_clicked)
        self.history_list.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        self.history_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.history_list.setWordWrap(True)
        self.history_list.setTextElideMode(Qt.ElideNone)
        sidebar_layout.addWidget(self.history_list, stretch=1)

        main_layout.addWidget(sidebar)

    def _setup_content(self, main_layout: QHBoxLayout) -> None:
        """우측 메인 컨텐츠 설정"""
        content = QWidget()
        content.setStyleSheet(f"background-color: {COLORS['canvas']};")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(28, 28, 28, 28)
        content_layout.setSpacing(20)

        self._setup_input_card(content_layout)
        self._setup_queue_card(content_layout)
        self._setup_result_card(content_layout)

        main_layout.addWidget(content, stretch=1)

    def _setup_input_card(self, content_layout: QVBoxLayout) -> None:
        """입력 카드 설정"""
        input_card = QFrame()
        input_card.setObjectName("card")
        input_card.setGraphicsEffect(create_shadow())
        input_card_layout = QVBoxLayout(input_card)
        input_card_layout.setContentsMargins(24, 24, 24, 24)
        input_card_layout.setSpacing(16)

        # 입력 필드 행
        input_row = QHBoxLayout()
        input_row.setSpacing(12)

        # 엔진 선택
        engine_group = QVBoxLayout()
        engine_group.setSpacing(6)
        engine_label = QLabel("AI 엔진")
        self.engine_combo = QComboBox()
        self.engine_combo.addItems(Generator.get_engine_names())
        engine_group.addWidget(engine_label)
        engine_group.addWidget(self.engine_combo)
        input_row.addLayout(engine_group)

        # 키워드 입력
        keyword_group = QVBoxLayout()
        keyword_group.setSpacing(6)
        keyword_label = QLabel("키워드 (입력 후 엔터로 추가)")
        self.keyword_input = QLineEdit()
        self.keyword_input.setPlaceholderText("키워드 입력 후 엔터")
        self.keyword_input.setAttribute(Qt.WA_InputMethodEnabled, True)
        self.keyword_input.returnPressed.connect(self._on_keyword_enter_delayed)
        keyword_group.addWidget(keyword_label)
        keyword_group.addWidget(self.keyword_input)
        input_row.addLayout(keyword_group, stretch=1)

        # 생성 버튼
        self.generate_btn = QPushButton("원고 생성")
        self.generate_btn.setMinimumHeight(52)
        self.generate_btn.setEnabled(False)
        self._update_generate_btn_style()
        self.generate_btn.clicked.connect(self._on_generate)
        input_row.addWidget(self.generate_btn, alignment=Qt.AlignBottom)

        input_card_layout.addLayout(input_row)

        # 키워드 칩 영역
        self.chips_container = QWidget()
        self.chips_layout = FlowLayout(self.chips_container)
        self.chips_layout.setContentsMargins(0, 0, 0, 0)
        self.chips_layout.setSpacing(8)
        self.chips_container.setVisible(False)
        input_card_layout.addWidget(self.chips_container)

        # 참조원고 토글
        self.ref_toggle_btn = QPushButton("+ 참조 원고 추가 (선택)")
        self.ref_toggle_btn.setObjectName("toggle")
        self.ref_toggle_btn.clicked.connect(self._toggle_ref_input)
        input_card_layout.addWidget(self.ref_toggle_btn)

        # 참조원고 입력 (기본 숨김)
        self.ref_container = QWidget()
        self.ref_container.setVisible(False)
        ref_layout = QVBoxLayout(self.ref_container)
        ref_layout.setContentsMargins(0, 0, 0, 0)
        ref_layout.setSpacing(6)

        self.ref_input = QTextEdit()
        self.ref_input.setPlaceholderText("참조할 원고가 있으면 여기에 붙여넣기")
        self.ref_input.setMaximumHeight(100)
        ref_layout.addWidget(self.ref_input)

        input_card_layout.addWidget(self.ref_container)

        content_layout.addWidget(input_card)

    def _setup_queue_card(self, content_layout: QVBoxLayout) -> None:
        """생성 큐 카드 설정"""
        self.queue_card = QFrame()
        self.queue_card.setObjectName("card")
        self.queue_card.setGraphicsEffect(create_shadow())
        self.queue_card.setVisible(False)
        queue_card_layout = QVBoxLayout(self.queue_card)
        queue_card_layout.setContentsMargins(24, 24, 24, 24)
        queue_card_layout.setSpacing(14)

        # 큐 헤더
        queue_header = QHBoxLayout()
        self.queue_title = QLabel("생성 진행 중...")
        self.queue_title.setObjectName("section_title")
        queue_header.addWidget(self.queue_title)
        queue_header.addStretch()

        self.stop_btn = QPushButton("중지")
        self.stop_btn.setObjectName("secondary")
        self.stop_btn.clicked.connect(self._on_stop_generate)
        queue_header.addWidget(self.stop_btn)

        queue_card_layout.addLayout(queue_header)

        # 큐 리스트
        self.queue_scroll = QScrollArea()
        self.queue_scroll.setWidgetResizable(True)
        self.queue_scroll.setMaximumHeight(200)
        self.queue_scroll.setStyleSheet(
            "QScrollArea { border: none; background: transparent; }"
        )

        self.queue_list_widget = QWidget()
        self.queue_list_layout = QVBoxLayout(self.queue_list_widget)
        self.queue_list_layout.setContentsMargins(0, 0, 0, 0)
        self.queue_list_layout.setSpacing(8)
        self.queue_list_layout.addStretch()

        self.queue_scroll.setWidget(self.queue_list_widget)
        queue_card_layout.addWidget(self.queue_scroll)

        content_layout.addWidget(self.queue_card)

    def _setup_result_card(self, content_layout: QVBoxLayout) -> None:
        """결과 카드 설정"""
        result_card = QFrame()
        result_card.setObjectName("card")
        result_card.setGraphicsEffect(create_shadow())
        result_card_layout = QVBoxLayout(result_card)
        result_card_layout.setContentsMargins(24, 24, 24, 24)
        result_card_layout.setSpacing(14)

        # 결과 헤더
        result_header = QHBoxLayout()
        result_header.setSpacing(10)

        result_title = QLabel("생성 결과")
        result_title.setObjectName("section_title")
        result_header.addWidget(result_title)

        self.category_label = QLabel("")
        self.category_label.setObjectName("badge")
        self.category_label.setVisible(False)
        result_header.addWidget(self.category_label)

        result_header.addStretch()

        self.char_count_label = QLabel("0자")
        self.char_count_label.setObjectName("char_count")
        result_header.addWidget(self.char_count_label)

        self.copy_btn = QPushButton("복사")
        self.copy_btn.setObjectName("secondary")
        self.copy_btn.setEnabled(False)
        self.copy_btn.clicked.connect(self._on_copy)
        result_header.addWidget(self.copy_btn)

        result_card_layout.addLayout(result_header)

        # 결과 출력
        self.result_output = QTextEdit()
        self.result_output.setReadOnly(True)
        self.result_output.setPlaceholderText(
            "키워드를 입력하고 원고 생성 버튼을 눌러주세요"
        )
        self.result_output.textChanged.connect(self._update_char_count)
        self.result_output.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        result_card_layout.addWidget(self.result_output, stretch=1)

        content_layout.addWidget(result_card, stretch=1)

    def _setup_status_bar(self) -> None:
        """상태바 설정"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(180)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.hide()
        self.status_bar.addPermanentWidget(self.progress_bar)

        self.status_bar.showMessage("준비됨")

    def _update_generate_btn_style(self) -> None:
        """생성 버튼 스타일 업데이트"""
        if self.is_generating:
            self.generate_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS["border"]};
                    border: none;
                    border-radius: 14px;
                    padding: 18px 40px;
                    color: {COLORS["text_muted"]};
                    font-size: 16px;
                    font-weight: 600;
                }}
            """)
        else:
            self.generate_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS["primary"]};
                    border: none;
                    border-radius: 14px;
                    padding: 18px 40px;
                    color: #FFFFFF;
                    font-size: 16px;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background-color: {COLORS["primary_hover"]};
                }}
                QPushButton:disabled {{
                    background-color: {COLORS["border"]};
                    color: {COLORS["text_muted"]};
                }}
            """)

    def _update_generate_btn_text(self) -> None:
        """생성 버튼 텍스트 업데이트"""
        count = len(self.keywords)
        if count == 0:
            self.generate_btn.setText("원고 생성")
            self.generate_btn.setEnabled(False)
        elif count == 1:
            self.generate_btn.setText("원고 생성")
            self.generate_btn.setEnabled(True)
        else:
            self.generate_btn.setText(f"{count}개 원고 생성")
            self.generate_btn.setEnabled(True)
        self._update_generate_btn_style()

    def _on_keyword_enter_delayed(self) -> None:
        """한글 IME 조합 대기"""
        QTimer.singleShot(50, self._add_keyword)

    def _add_keyword(self) -> None:
        """키워드 추가"""
        keyword = self.keyword_input.text().strip()
        if not keyword:
            return

        if keyword in self.keywords:
            self.status_bar.showMessage("이미 추가된 키워드입니다", 2000)
            return

        self.keywords.append(keyword)

        chip = KeywordChip(keyword)
        chip.removed.connect(self._remove_keyword)
        self.keyword_chips[keyword] = chip
        self.chips_layout.addWidget(chip)

        self.chips_container.setVisible(True)
        self.keyword_input.clear()
        self._update_generate_btn_text()

        self.status_bar.showMessage(
            f"'{keyword}' 추가됨 (총 {len(self.keywords)}개)", 2000
        )

    def _remove_keyword(self, keyword: str) -> None:
        """키워드 제거"""
        if keyword in self.keywords:
            self.keywords.remove(keyword)

        if keyword in self.keyword_chips:
            chip = self.keyword_chips.pop(keyword)
            self.chips_layout.removeWidget(chip)
            chip.deleteLater()

        if not self.keywords:
            self.chips_container.setVisible(False)

        self._update_generate_btn_text()

    def _toggle_ref_input(self) -> None:
        """참조 원고 토글"""
        self.ref_expanded = not self.ref_expanded
        self.ref_container.setVisible(self.ref_expanded)

        if self.ref_expanded:
            self.ref_toggle_btn.setText("- 참조 원고 접기")
        else:
            self.ref_toggle_btn.setText("+ 참조 원고 추가 (선택)")

    def _load_history_from_db(self) -> None:
        """DB에서 히스토리 로드"""
        try:
            import sys
            from pathlib import Path

            project_root = Path(__file__).parent.parent.parent
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))

            from mongodb_service import MongoDBService

            self.history.clear()
            self.history_list.clear()

            db_service = MongoDBService()

            try:
                db_names = db_service.client.list_database_names()
                system_dbs = ["admin", "local", "config"]
                category_dbs = [db for db in db_names if db not in system_dbs]

                all_manuscripts = []
                for db_name in category_dbs:
                    db_service.set_db_name(db_name)
                    docs = list(
                        db_service.db["manuscripts"]
                        .find(
                            {},
                            {
                                "content": 1,
                                "keyword": 1,
                                "engine": 1,
                                "category": 1,
                                "createdAt": 1,
                            },
                        )
                        .sort("createdAt", -1)
                        .limit(5)
                    )
                    all_manuscripts.extend(docs)

                all_manuscripts.sort(
                    key=lambda x: x.get("createdAt", datetime.min), reverse=True
                )

                for doc in all_manuscripts[:20]:
                    item = HistoryItem(
                        keyword=doc.get("keyword", ""),
                        category=doc.get("category", "기타"),
                        engine=doc.get("engine", ""),
                        content=doc.get("content", ""),
                        created_at=doc.get("createdAt", datetime.now()),
                    )
                    self.history.append(item)

                    list_item = QListWidgetItem()
                    keyword_text = (
                        item.keyword[:20] + "..."
                        if len(item.keyword) > 20
                        else item.keyword
                    )
                    time_str = (
                        item.created_at.strftime("%m/%d %H:%M")
                        if item.created_at
                        else ""
                    )
                    list_item.setText(f"{keyword_text}\n{item.category}  ·  {time_str}")
                    self.history_list.addItem(list_item)

                self.status_bar.showMessage(f"최근 {len(self.history)}개", 2000)

            finally:
                db_service.close_connection()

        except Exception:
            self.status_bar.showMessage("히스토리 로드 실패", 3000)

    def _on_history_clicked(self, item: QListWidgetItem) -> None:
        """히스토리 클릭 핸들러"""
        idx = self.history_list.row(item)
        if 0 <= idx < len(self.history):
            history_item = self.history[idx]
            self.result_output.setPlainText(history_item.content)
            self.category_label.setText(history_item.category)
            self.category_label.setVisible(True)
            self.copy_btn.setEnabled(True)
            self.status_bar.showMessage(f"'{history_item.keyword}' 불러옴", 2000)

    def _on_generate(self) -> None:
        """생성 시작"""
        if not self.keywords:
            return

        engine = self.engine_combo.currentText()
        ref = self.ref_input.toPlainText().strip() if self.ref_expanded else ""

        self.is_generating = True
        self.generate_btn.setEnabled(False)
        self.generate_btn.setText("생성 중...")
        self._update_generate_btn_style()

        self.progress_bar.setRange(0, len(self.keywords))
        self.progress_bar.setValue(0)
        self.progress_bar.show()

        # 큐 UI 설정
        self._clear_queue()
        for idx, keyword in enumerate(self.keywords):
            queue_item = QueueItem(keyword, idx)
            self.queue_items.append(queue_item)
            self.queue_list_layout.insertWidget(idx, queue_item)

        self.queue_card.setVisible(True)
        self.queue_title.setText(f"생성 진행 중... (0/{len(self.keywords)})")
        self.results.clear()

        self.status_bar.showMessage(
            f"{engine}으로 {len(self.keywords)}개 원고 생성 시작..."
        )

        self.worker = BatchGenerateWorker(engine, self.keywords.copy(), ref)
        self.worker.item_started.connect(self._on_item_started)
        self.worker.item_finished.connect(self._on_item_finished)
        self.worker.item_error.connect(self._on_item_error)
        self.worker.all_finished.connect(self._on_all_finished)
        self.worker.start()

    def _on_stop_generate(self) -> None:
        """생성 중지"""
        if self.worker:
            self.worker.stop()
            self.status_bar.showMessage("생성 중지 요청됨...", 2000)

    def _on_item_started(self, idx: int) -> None:
        """아이템 생성 시작"""
        if 0 <= idx < len(self.queue_items):
            self.queue_items[idx].set_status("running")

    def _on_item_finished(self, idx: int, result: str, category: str) -> None:
        """아이템 생성 완료"""
        if 0 <= idx < len(self.queue_items):
            char_count = len(result.replace(" ", "").replace("\n", ""))
            self.queue_items[idx].set_status("done", f"완료 ({char_count:,}자)")
            self.results[idx] = (result, category)

        completed = sum(
            1 for item in self.queue_items if item.status in ("done", "error")
        )
        self.progress_bar.setValue(completed)
        self.queue_title.setText(
            f"생성 진행 중... ({completed}/{len(self.keywords)})"
        )

        # 첫 번째 결과 표시
        if idx == 0:
            self.result_output.setPlainText(result)
            self.category_label.setText(category)
            self.category_label.setVisible(True)
            self.copy_btn.setEnabled(True)

    def _on_item_error(self, idx: int, error: str) -> None:
        """아이템 생성 에러"""
        if 0 <= idx < len(self.queue_items):
            self.queue_items[idx].set_status("error", error)

        completed = sum(
            1 for item in self.queue_items if item.status in ("done", "error")
        )
        self.progress_bar.setValue(completed)
        self.queue_title.setText(
            f"생성 진행 중... ({completed}/{len(self.keywords)})"
        )

    def _on_all_finished(self) -> None:
        """모든 생성 완료"""
        done_count = sum(1 for item in self.queue_items if item.status == "done")
        error_count = sum(1 for item in self.queue_items if item.status == "error")

        self.queue_title.setText(
            f"완료 · {done_count}개 성공"
            + (f", {error_count}개 실패" if error_count else "")
        )

        self._reset_ui()

        # 키워드 칩 초기화
        for keyword in list(self.keyword_chips.keys()):
            self._remove_keyword(keyword)

        # 히스토리에 추가
        engine = self.engine_combo.currentText()
        for idx in sorted(self.results.keys()):
            result, category = self.results[idx]
            keyword = self.keywords[idx] if idx < len(self.keywords) else ""

            new_item = HistoryItem(
                keyword=keyword,
                category=category,
                engine=engine,
                content=result,
                created_at=datetime.now(),
            )
            self.history.insert(0, new_item)

            list_item = QListWidgetItem()
            keyword_text = keyword[:20] + "..." if len(keyword) > 20 else keyword
            time_str = datetime.now().strftime("%m/%d %H:%M")
            list_item.setText(f"{keyword_text}\n{category}  ·  {time_str}")
            self.history_list.insertItem(0, list_item)

        self.keywords.clear()
        self._update_generate_btn_text()

        self.status_bar.showMessage(f"완료 · {done_count}개 생성됨", 3000)

    def _clear_queue(self) -> None:
        """큐 초기화"""
        for item in self.queue_items:
            self.queue_list_layout.removeWidget(item)
            item.deleteLater()
        self.queue_items.clear()

    def _reset_ui(self) -> None:
        """UI 초기화"""
        self.is_generating = False
        self.generate_btn.setEnabled(len(self.keywords) > 0)
        self._update_generate_btn_text()
        self.progress_bar.hide()
        self.worker = None

    def _on_copy(self) -> None:
        """결과 복사"""
        text = self.result_output.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            self.status_bar.showMessage("클립보드에 복사됨", 2000)

    def _update_char_count(self) -> None:
        """글자수 업데이트"""
        text = self.result_output.toPlainText()
        char_count = len(text.replace(" ", "").replace("\n", ""))
        self.char_count_label.setText(f"{char_count:,}자")
