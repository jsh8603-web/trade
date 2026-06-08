---
tags: [type/candidate-ledger, domain/equity-us, sector/xlf_financials, purpose/easy-review]
date: 2026-06-08
status: ★PASSIVE 확정 (minimal verify) — value/quality 전 factor 비유의. early-stop 후보.
---

# XLF(금융) 후보 원장 (minimal verify, §13 VERIFY 1순위)

## 🏁 ★최종 결론

★**XLF selection = PASSIVE 확정** (null result). sleeve = top 시총 동일가중 passive(SOXX 동형).
- value(P/B·P/TBV) + quality(ROE·ROIC) **전 factor non-overlap t<2** (최대 quality_roic t=0.84) = signal 부재.
- ★생존편향 upper-bound(2023 파산은행 SVB/Signature/FRC 누락 → value-IC 부풀려진 상태)인데도 비유의 = value 확실 부재.
- ★§13 VERIFY 1순위(양 모델 유일 진짜 후보)조차 무너짐 = 미국 GICS selection 무료데이터 ★early-stop 후보(XLI 2순위 미검증).

## 📊 측정 verdict (validation-xlf.json)

| factor | y60 IC | non-overlap t | verdict |
|---|---|---|---|
| value (P/B·P/TBV) | 0.019 | 0.45 | 비유의 |
| value_pb | 0.011 | 0.06 | 비유의 |
| value_ptbv | 0.028 | 0.63 | 비유의(최강 value이나 t<2) |
| quality_roe | 0.016 | 0.28 | 비유의 |
| quality_roic | 0.061 | 0.84 | 비유의(최대 IC이나 t<2) |

- ★leave-top2-out(BRK-B·JPM) retention y60=0.55 = kill 게이트 PASS이나 ★IC 자체가 ~0이라 무의미(SOXX는 IC 컸으나 2-name; XLF는 IC 부재).

## ❌ 미채택 (전 factor REJECTED)
- value/quality 전부 non-overlap t<2 비유의. EV/EBITDA = 금융 무의미(미사용).

## 🔓 Reopen 트리거 (§방향보존)
- ⛔ "금융 value 영구 무효" 아님 = 현 무료-데이터 틀(현-holdings, 파산은행 누락) 코드화 불가 = 범위한정.
- ★Reopen = 생존편향-free CRSP universe(파산은행 포함) 확보 시 재검토. 현 = data-gate(CRSP 유료).

## ⚠️ sub-industry caveat
- 은행(P/B 유효) / 보험(P/TBV 유효) / 결제네트워크 V/MA(자본경량 P/B 무의미) / 자본시장 = 이질성. minimal=전체 적용+flag.
