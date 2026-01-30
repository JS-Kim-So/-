# Electric Item Generator (v0.1.0)

전기 공급만으로 생존용 아이템을 생산하는 설치형 제작기(기계) 모드입니다.

한국어 설명서는 `README_KO.md`를 참고하세요.
배포용 ZIP은 `pack_mod.sh`로 생성할 수 있습니다.
DLL 빌드 방법도 `README_KO.md`에 단계별로 정리했습니다.

## 설치 방법

1. `Mods/ElectricItemGenerator` 폴더를 7 Days to Die의 `Mods` 디렉터리에 복사합니다.
2. C# 코드를 빌드해 `Mods/ElectricItemGenerator/bin`에 DLL을 배치합니다.
3. 게임 실행 후 창고/워크벤치에서 `전기 아이템 생성기`를 제작합니다.

## 빌드 방법 (C#)

- Visual Studio 또는 Rider에서 `Mods/ElectricItemGenerator/Scripts` 폴더를 클래스 라이브러리 프로젝트로 열고,
  7 Days to Die의 `Managed` DLL을 참조합니다.
  - 필수 참조(예): `Assembly-CSharp.dll`, `UnityEngine.dll`, `UnityEngine.CoreModule.dll`
- 빌드 산출물 DLL을 `Mods/ElectricItemGenerator/bin/ElectricItemGenerator.dll`로 복사합니다.

## 테스트 방법

1. 크리에이티브 또는 생존 모드에서 `전기 아이템 생성기`를 설치합니다.
2. 발전기/전선으로 전력을 연결하고 스위치를 ON 합니다.
3. UI에서 생산할 아이템을 선택합니다.
4. 출력 슬롯으로 아이템이 생성되는지 확인합니다.

## 필수 테스트 시나리오

- 전기 ON → 아이템 선택 → 생산 시작
- 생산 중 전기 OFF → 즉시 일시정지
- 다시 전기 ON → 동일 진행률에서 생산 재개
- 출력 슬롯 가득 참 → 생산 중지
- 슬롯 비움 → 생산 재개
- 세이브 후 로드 → 진행 상태 유지 확인

## 생산 테이블

`Config/eig_production_table.json`에서 카테고리/아이템/제작 시간을 편집할 수 있습니다.

- `powerConsumption`: 기본 전력 소모 (W)
- `outputSlots`: 출력 슬롯 수
- `queueSize`: 생산 큐 크기

## UI 구조 메모

- v1에서는 기본 작업대 UI(`workstation`)를 호출하도록 구성했습니다.
- 카테고리 기반 UI를 구현하려면 전용 XUi 윈도우 및 컨트롤러를 추가하고
  `TileEntityElectricItemGenerator.OpenUi()`를 그 윈도우로 교체하면 됩니다.
