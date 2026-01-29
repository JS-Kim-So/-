# Electric Item Generator (전기 아이템 생성기) 설명서

이 문서는 7 Days to Die(PC Steam 최신 버전)용 모드 **Electric Item Generator**의 기능과 설정 방법을 한글로 정리한 안내서입니다.

## 1. 모드 개요

- **목표:** 전기 공급만으로 생존용 아이템을 생산하는 설치형 제작기(기계)를 추가합니다.
- **입력 재료/연료:** 없음
- **작동 조건:** 전기 ON
- **전기 OFF:** 즉시 생산 일시정지
- **재전력 ON:** 진행률 유지한 채 생산 재개
- **출력 슬롯 가득 참:** 생산 일시정지 → 슬롯 비우면 자동 재개

## 2. 모드 구조

```
Mods/ElectricItemGenerator/
├─ Config/
│  ├─ blocks.xml
│  ├─ items.xml
│  ├─ recipes.xml
│  ├─ localization.txt
│  └─ eig_production_table.json
├─ Scripts/
│  ├─ ElectricItemGeneratorMod.cs
│  ├─ ProductionTable.cs
│  ├─ BlockElectricItemGenerator.cs
│  └─ TileEntityElectricItemGenerator.cs
├─ ModInfo.xml
├─ README.md
└─ README_KO.md
```

## 3. 설치 방법

1. `Mods/ElectricItemGenerator` 폴더를 7 Days to Die의 `Mods` 디렉터리에 복사합니다.
2. C# 코드를 빌드해 DLL을 `Mods/ElectricItemGenerator/bin/ElectricItemGenerator.dll`로 배치합니다.
3. 게임 실행 후 워크벤치에서 `전기 아이템 생성기`를 제작합니다.

### 쉬운 설치(압축 배포용 구조)

다음과 같은 폴더 구조를 그대로 `Mods` 폴더 아래에 넣으면 됩니다.

```
7 Days To Die/
└─ Mods/
   └─ ElectricItemGenerator/
      ├─ Config/
      ├─ Scripts/
      ├─ ModInfo.xml
      ├─ README.md
      └─ README_KO.md
```

> ⚠️ 이 모드는 C# DLL이 있어야 정상 동작합니다.
> 빌드가 어려운 경우, `bin/ElectricItemGenerator.dll`이 포함된 압축본을 받으면 됩니다.

### 간편 ZIP 만들기(배포용)

빌드된 DLL이 `Mods/ElectricItemGenerator/bin`에 있다고 가정하면,
아래 스크립트로 모드 ZIP을 만들 수 있습니다.

```bash
cd Mods/ElectricItemGenerator
./pack_mod.sh
```

완성된 ZIP 파일은 `Mods/ElectricItemGenerator.zip`에 생성됩니다.

## 4. 제작(레시피) 정보

- 제작대: **워크벤치**
- 재료(기본값):
  - forgedIron x30
  - electricalParts x20
  - mechanicalParts x10
  - ductTape x10
  - spring x10
  - oil x5

> 위 재료와 수치는 `Config/recipes.xml`에서 변경할 수 있습니다.

## 5. 전기/작동 규칙

- 전력 소비: 기본 10W (변경 가능)
- 전기 ON → 생산 진행
- 전기 OFF → 생산 일시정지 (진행률 유지)
- 출력 슬롯 가득 참 → 생산 정지 (슬롯 비우면 자동 재개)

## 6. 생산 테이블(아이템 목록/시간)

`Config/eig_production_table.json`에서 카테고리 기반으로 아이템과 제작 시간을 관리합니다.

- `powerConsumption`: 기본 전력 소모 (W)
- `outputSlots`: 출력 슬롯 수
- `queueSize`: 생산 큐 크기(현재 1칸 사용)
- `categories`: 카테고리 목록
  - `id`: 내부 식별자
  - `label`: 표시용 이름
  - `items`: 아이템 리스트
    - `item`: 아이템 이름(게임 내 ID)
    - `craftTimeSeconds`: 제작 시간(초)

### 예시
```json
{
  "id": "ingots",
  "label": "Ingots",
  "items": [
    {"item": "iron", "craftTimeSeconds": 20},
    {"item": "steel", "craftTimeSeconds": 100}
  ]
}
```

## 7. 데이터 유지(세이브/로드)

다음 정보가 저장되어 세이브/로드 후에도 복원됩니다.

- 선택된 아이템
- 현재 생산 진행률
- 전기 상태에 따른 일시정지 여부
- 출력 슬롯 아이템

## 8. UI 안내

- v1 기준으로 **기본 작업대 UI(`workstation`)**를 호출하도록 구성했습니다.
- 카테고리 기반 UI를 직접 구현하려면 XUi 윈도우/컨트롤러를 추가하고,
  `TileEntityElectricItemGenerator.OpenUi()`를 새 창으로 교체하면 됩니다.

## 9. 필수 테스트 시나리오

1. 전기 ON → 아이템 선택 → 생산 시작
2. 생산 중 전기 OFF → 즉시 일시정지
3. 다시 전기 ON → 동일 진행률에서 생산 재개
4. 출력 슬롯 가득 참 → 생산 중지
5. 슬롯 비움 → 생산 재개
6. 세이브 후 로드 → 진행 상태 유지 확인

## 10. 변경 포인트 요약

- **아이템/제작 시간**: `Config/eig_production_table.json`
- **전력 소모**: `Config/eig_production_table.json` 또는 `Config/blocks.xml`
- **레시피 재료**: `Config/recipes.xml`
- **표시 이름/설명**: `Config/localization.txt`

## 11. 알려진 제한 (v0.1)

- 전용 UI 미구현(기본 작업대 UI 사용)
- 생산 큐 1칸만 사용
- 생산 중 기계 파괴 시 진행 중이던 생산은 소멸 처리

필요 시 다음 단계에서 전용 UI와 세부 밸런스 튜닝을 확장할 수 있습니다.
