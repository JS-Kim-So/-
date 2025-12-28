# Inventory MVP-1

FastAPI 기반 재고 관리 MVP-1 구현입니다. 기본 API 문서는 `/docs`에서 확인할 수 있습니다.

## 실행

```bash
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

## 기본 기능

- 제품군/제품/로트 마스터 CRUD
- 입고/출고 전표 생성(로트 필수, 수량 정수, 음수 재고 허용)
- 현재고/입출고 이력 조회
- 전표 수정 + 감사로그 기록
- 전표 삭제 금지(DB 트리거)

## 확장 항목(미구현)

- 취소전표(REVERSAL) 기반 취소 처리
- 사용자/권한(관리자/담당자/조회)
- 멀티 창고/로케이션
- 엑셀 Import/Export
- 원가/단가/정산 연동
