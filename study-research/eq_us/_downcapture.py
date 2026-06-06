# -*- coding: utf-8 -*-
"""_downcapture.py — "불경기 방어주" 정설 검정 영속 스크립트 (2026-06-04).

reflection-verify 지적(down-capture 0.57 산출이 /tmp 비영속)에 대응한 영속화.
정설 진짜 명세 = down-capture<1 (시장 하락 때 덜 빠짐). regime-split excess 측정(∑excess≡0
항등식 artifact)이 아니라 down-capture 로 검정해야 정설을 옳게 본다(empirical-claim §1.8).

정의: market = shrunk inverse-vol base portfolio return. 하락월(market<0)에서
  down_capture(sleeve) = mean(sleeve_ret | market<0) / mean(market_ret | market<0).
  <1 = 시장보다 덜 빠짐(방어). >1 = 더 빠짐(공격).

★self-referential 주의: market 이 3 sleeve 가중평균이라 base 내장 sleeve 비교는 상대값.
  단 down-capture 는 excess(∑≡0)와 달리 "하락 절대 동행성"이라 정설(하락방어) 직격 가능.

재현: python _downcapture.py  (합성 0 = 실 prices, go-live 무접촉)
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _sleeve_rotation as SR


def main():
    ret = SR.load_sleeve_monthly_ret()          # month-end, 3 sleeve EW return
    w = SR.shrunk_inverse_vol(ret)               # base 비중 (cyc/def/mega)
    market = (ret * w).sum(axis=1)               # base portfolio return = 시장 proxy
    down = market < 0
    n_down = int(down.sum())

    print("=" * 64)
    print(f"down-capture (시장=shrunk inverse-vol base, 하락월 n={n_down}/{len(market)})")
    print(f"  시장 하락월 평균 = {market[down].mean()*100:+.2f}%/월")
    print("-" * 64)
    print(f"  {'sleeve':<16}{'base_w':>8}{'down월 평균':>12}{'down-capture':>14}{'판정':>8}")
    for i, sl in enumerate(ret.columns):
        dc = ret.loc[down, sl].mean() / market[down].mean()
        verdict = "방어" if dc < 0.9 else ("중립" if dc < 1.1 else "공격")
        print(f"  {sl:<16}{w[i]:>8.3f}{ret.loc[down, sl].mean()*100:>11.2f}%{dc:>14.2f}{verdict:>8}")
    print("=" * 64)
    print("정설('불경기 방어주') = defensive down-capture < 1 이면 robust (시장 하락 절반 방어).")
    print("이는 excess(∑w·excess≡0 항등식)와 다른 축 — regime-split '정설 반대'는 측정 명세오류.")


if __name__ == "__main__":
    main()
