# 코드 개선 보고서

> 분석 일자: 2025-12-01
> 분석 대상: `program/` 디렉토리 (PySide6 GUI 애플리케이션)

---

## 요약

| 심각도 | 개수 | 설명 |
|--------|------|------|
| 🔴 Critical | 1 | 런타임 충돌 가능성 |
| 🟠 High | 1 | 디버깅 어려움 |
| 🟡 Medium | 2 | 유지보수성 저하 |
| 🟢 Low | 3 | 코드 품질 개선 |

---

## 🔴 Critical Issues

### 1. QThread 내부에서 asyncio.run() 호출

**파일**: `program/core/generator.py:51`

**문제점**:
- `asyncio.run()`은 새로운 이벤트 루프를 생성하는데, 이미 실행 중인 루프가 있으면 `RuntimeError` 발생
- PySide6의 QThread에서 호출 시 이벤트 루프 충돌 가능성

**현재 코드**:
```python
@classmethod
def _get_category(cls, keyword: str, ref: str = "") -> str:
    text = keyword + ref
    try:
        return asyncio.run(get_category_db_name(keyword=text))
    except Exception:
        return "기타"
```

**개선 방안**:
```python
@classmethod
def _get_category(cls, keyword: str, ref: str = "") -> str:
    text = keyword + ref
    try:
        # 이미 실행 중인 루프가 있는지 확인
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop is not None:
            # 이미 루프가 실행 중이면 동기 버전 사용 또는 nest_asyncio
            import nest_asyncio
            nest_asyncio.apply()
            return asyncio.run(get_category_db_name(keyword=text))
        else:
            return asyncio.run(get_category_db_name(keyword=text))
    except Exception as e:
        logging.warning(f"카테고리 추출 실패: {e}")
        return "기타"
```

**또는 근본적 해결**:
```python
# get_category_db_name을 동기 버전으로 제공하거나
# Generator.generate()를 async로 변경
```

---

## 🟠 High Priority Issues

### 2. 예외 처리 시 로깅 없음

**파일**:
- `program/core/generator.py:52`
- `program/ui/workers.py:43`

**문제점**:
- 예외 발생 시 원인 파악이 어려움
- 디버깅 시간 증가

**현재 코드**:
```python
# generator.py
except Exception:
    return "기타"

# workers.py
except Exception as e:
    self.item_error.emit(idx, str(e))
```

**개선 방안**:
```python
import logging

logger = logging.getLogger(__name__)

# generator.py
except Exception as e:
    logger.exception(f"카테고리 추출 실패 (keyword={keyword})")
    return "기타"

# workers.py
except Exception as e:
    logger.exception(f"생성 실패 (keyword={keyword})")
    self.item_error.emit(idx, str(e))
```

---

## 🟡 Medium Priority Issues

### 3. 모듈 레벨 sys.path 조작

**파일**: `program/core/generator.py:8-10`

**문제점**:
- 전역 상태 변경으로 사이드 이펙트 발생 가능
- 다른 모듈과 충돌 가능성
- 테스트 격리 어려움

**현재 코드**:
```python
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
```

**개선 방안**:
1. **pyproject.toml 사용** (권장):
```toml
[tool.setuptools.packages.find]
where = ["."]
```

2. **상대 임포트 사용**:
```python
from ...llm.grok_service import grok_gen
```

3. **PYTHONPATH 환경변수 설정**:
```bash
export PYTHONPATH="${PYTHONPATH}:/path/to/blog_analyzer"
```

---

### 4. 중복된 상태 관리 패턴

**파일**: `program/ui/main_window.py`

**문제점**:
- `self.keywords`와 `self.keyword_chips`가 동기화 필요
- 상태 불일치 가능성

**현재 코드**:
```python
self.keywords: list[str] = []
self.keyword_chips: dict[str, KeywordChip] = {}
```

**개선 방안**:
```python
# 단일 소스로 관리
class KeywordManager:
    def __init__(self):
        self._chips: dict[str, KeywordChip] = {}

    @property
    def keywords(self) -> list[str]:
        return list(self._chips.keys())

    def add(self, keyword: str, parent: QWidget) -> KeywordChip:
        if keyword in self._chips:
            return self._chips[keyword]
        chip = KeywordChip(keyword, parent)
        self._chips[keyword] = chip
        return chip

    def remove(self, keyword: str) -> None:
        if keyword in self._chips:
            chip = self._chips.pop(keyword)
            chip.deleteLater()
```

---

## 🟢 Low Priority Issues

### 5. 미사용 파라미터

**파일**: `program/ui/widgets/queue_item.py:14`

**문제점**:
- `index` 파라미터가 저장만 되고 사용되지 않음

**현재 코드**:
```python
def __init__(self, keyword: str, index: int, parent=None):
    super().__init__(parent)
    self.keyword = keyword
    self.index = index  # 미사용
```

**개선 방안**:
```python
# 사용하지 않으면 제거
def __init__(self, keyword: str, parent=None):
    super().__init__(parent)
    self.keyword = keyword

# 또는 디버깅/접근성에 활용
def __init__(self, keyword: str, index: int, parent=None):
    super().__init__(parent)
    self.keyword = keyword
    self.index = index
    self.setAccessibleName(f"Queue item {index}: {keyword}")
```

---

### 6. 매직 넘버 사용

**파일**: `program/ui/main_window.py`

**문제점**:
- 타임아웃 값(50, 2000, 3000ms)이 하드코딩됨
- 의미 파악 어려움

**개선 방안**:
```python
# styles.py 또는 constants.py에 정의
class Timing:
    IME_DELAY_MS = 50
    TOAST_SHORT_MS = 2000
    TOAST_LONG_MS = 3000
    ANIMATION_DURATION_MS = 200
```

---

### 7. 타입 힌트 누락

**파일**: 여러 파일

**문제점**:
- `parent` 파라미터에 타입 힌트 없음
- IDE 자동완성 지원 저하

**현재 코드**:
```python
def __init__(self, keyword: str, parent=None):
```

**개선 방안**:
```python
from PySide6.QtWidgets import QWidget

def __init__(self, keyword: str, parent: QWidget | None = None):
```

---

## 개선 로드맵

### Phase 1: 안정성 (즉시)
- [ ] asyncio.run() 이슈 해결
- [ ] 로깅 추가

### Phase 2: 유지보수성 (단기)
- [ ] sys.path 조작 제거
- [ ] 상태 관리 통합

### Phase 3: 코드 품질 (중기)
- [ ] 미사용 코드 정리
- [ ] 상수 분리
- [ ] 타입 힌트 완성

---

## 참고

- 분석 도구: Claude Code (Opus 4.5)
- 대상 파일:
  - program/ui/main_window.py
  - program/ui/workers.py
  - program/ui/widgets/*.py
  - program/core/generator.py
