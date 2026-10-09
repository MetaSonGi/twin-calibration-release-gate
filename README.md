# 트윈 보정 배포 검증기

학습 구간에서 예측 편향 보정값을 구하고 별도의 시간 후행 검증 구간에서 개선·오차·보정 한도를 모두 통과해야 후보를 승인합니다.

## 핵심 기능

보정값은 학습 구간만 사용해 median(observed-predicted)으로 구합니다. 보정값 크기·후행 검증 MAE·절대 개선량을 모두 검사합니다. 승인 결과도 배포하지 않으며 applied_to_production=false를 반환합니다. 기존 온도 모니터와 달리 모델 버전 변경의 품질 게이트를 구현합니다.

## 설치·실행

Python 3.10 이상. 외부 패키지·API 키·장비 연결이 필요 없습니다.

```bash
git clone https://github.com/MetaSonGi/twin-calibration-release-gate.git
cd twin-calibration-release-gate
python -m pip install -r requirements.txt
python main.py
python main.py --input sample-input.json --html result.html
python -m unittest -v
```

Windows에서 python 대신 py를 사용할 수 있습니다. 다른 디렉터리에서 실행해도 기본 샘플은 main.py 옆 파일에서 읽습니다. 모든 출력 파일 경로는 명시한 위치에 생성합니다.

## 웹에서 결과 확인

다운로드한 `example-report.html`을 브라우저에서 열면 검증한 샘플 결과가 보입니다. 입력을 수정하고 `python main.py --input sample-input.json --html result.html`을 실행하면 새 결과를 브라우저로 볼 수 있습니다. 보고서는 HTML에 결과를 포함하므로 네트워크·CDN·서버가 필요 없습니다. 입력 문자열은 escape해 HTML/스크립트로 실행하지 않습니다. 이는 입력 편집용 웹 앱이 아닌 실행 결과 뷰어입니다.

## 입력·출력 예제

합성 입력: [sample-input.json](sample-input.json). 필드와 형식은 이 파일이 최소 실행 예제입니다. 반환 규칙은 main.py의 `run(data)`에 정의됩니다. 손상된 JSON·필수 필드 누락·잘못된 수치 입력은 CLI가 종료 코드 2로 보고합니다.

```json
{
  "train": [
    {
      "time_s": 0,
      "observed": 22,
      "predicted": 20
    },
    {
      "time_s": 1,
      "observed": 23,
      "predicted": 21
    },
    {
      "time_s": 2,
      "observed": 24,
      "predicted": 22
    },
    {
      "time_s": 3,
      "observed": 25,
      "predicted": 23
    }
  ],
  "validation": [
    {
      "time_s": 4,
      "observed": 26.1,
      "predicted": 24
    },
    {
      "time_s": 5,
      "observed": 27.1,
      "predicted": 25
    },
    {
      "time_s": 6,
      "observed": 28.1,
      "predicted": 26
    }
  ],
  "max_offset": 3,
  "max_validation_mae": 0.3,
  "min_improvement": 0.5
}
```

출력 미리보기(생략 표시 부분은 설명이며 JSON 입력으로 사용하지 마세요):

```text
{
  "approved": true,
  "reasons": [],
  "proposed_offset": 2.0,
  "baseline_validation_mae": 2.1,
  "candidate_validation_mae": 0.1,
  "absolute_improvement": 2.0,
  "training_samples": 4,
  "validation_samples": 3,
  "applied_to_production": false,
  "method": "training_median_residual_offset"
}
```

전체 실행 결과: [example-output.json](example-output.json), [example-report.html](example-report.html).

## 설계 판단·통합

보정값은 학습 구간만 사용해 median(observed-predicted)으로 구합니다. 보정값 크기·후행 검증 MAE·절대 개선량을 모두 검사합니다. 승인 결과도 배포하지 않으며 applied_to_production=false를 반환합니다. 기존 온도 모니터와 달리 모델 버전 변경의 품질 게이트를 구현합니다.

장비 데이터 수집 계층에서 합성 예제를 실제 데이터 스키마로 변환한 뒤 `run(data)`를 호출할 수 있습니다. Nest.js/Python 작업 큐 또는 테스트 자동화에서 JSON 입출력을 사용하고 XR/WebGL 화면에는 검증된 결과만 표시하는 방식으로 연결할 수 있습니다. 프로그램에는 실제 제어·유료 서비스·사용자 계정 접근 코드가 없습니다.

## 한계

한 개 스칼라의 일정 편향만 보정합니다. 불확실성 추정·통계적 유의성·환경별 공정성·온라인 드리프트·모델 자동 배포는 포함하지 않습니다. 실무 적용에는 긴 검증 구간과 여러 운전 조건이 필요합니다.

가상의 경력, 논문 성능 수치, 모델 재현 또는 실물 제조 검증을 주장하지 않습니다. 데이터가 합성 예제인 만큼 현장 적용 전 데이터 품질·운영 조건을 다시 검증해야 합니다.

## 검증·근거

의미 있는 정상·경계·오류 테스트 4개를 실제 실행했습니다. 기록은 [VALIDATION.txt](VALIDATION.txt)에 있습니다. 논문 날짜·상태·확인 범위와 개발자 해석은 [TRENDS.md](TRENDS.md)를 참고하세요.

실행 기준일: 2026-10-09 (Asia/Seoul). 기존 저장소를 수정하지 않고 독립 프로그램으로 구성했습니다.
