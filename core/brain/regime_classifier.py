"""
regime_classifier.py — 거시 레짐 분류기 (brain 결정론 baseline, 매 사이클 무료 실행).

설계 정합 (§5.8-A, §5.8-B, §5.8-F):
- Investment Clock(성장×인플레 4분면; FRED 실질GDP·코어CPI) — 결정론 baseline (§5.8-A).
- JM/SJM (jumpmodels, Apache-2.0) — HMM 일반화, sparse/고차원/상태지속성 강건 (§5.8-A R10).
- HMM 비교 폴백 (hmmlearn) — JM 와 발산 시 §5.8-H 오판 탐지 채널.
- classifier(regime_now) ≠ forecaster(regime_forecast) 필드 분리 (§5.8-A).
- per-bloc (USD/KRW 독립). FRED-MD(1959+) 장기훈련 가정 — sparse 아님 (§5.8-A R10).
- NBER lag 분리: 학습 라벨만, 실시간 추론엔 FRED-MD+Sahm+나우캐스팅 (§5.8-A, §5.8-F).
- 출력 = MacroView (regime_now + regime_forecast + status + age + 근거 + 인용ID).

코드화한 macro.md:
- Investment Clock 4분면 매핑 = macro_indicators.investment_clock_quadrant.
- Michez/Sahm/금리커브/GDP-GDI/Truflation = macro_indicators 호출로 evidence·confidence 보정.

github 차용 (입출력 계약 확인 후 어댑트):
- jumpmodels/jump.py:JumpModel — `.fit(X, ret_ser, sort_by)` → labels_/transmat_, `.predict_online()`.
- jumpmodels/sparse_jump.py:SparseJumpModel — `max_feats` 피처선택 (거시 지표 자동 선별).
- jumpmodels/preprocess.py:StandardScalerPD, DataClipperStd — 표준화/클리핑 전처리.
- forecasting repo 방법론(FRED-MD+NBER+ℓ1-trend) = macro.md 흡수분, 라벨링 전략에 반영.

정직한 한계 (§5.8-A):
- 비정상성(60년 ≠ i.i.d.) → 긴 역사 도움이나 공짜 아님; JM 도 PBO/과적합(H23) 적용.
- NBER 라벨 후행 → 학습 전용. JM 미설치 시 규칙(4분면) 단독으로 graceful degrade.

미해결 결정:
- JM n_components: 2(bull/bear) vs 4(IC 4분면). 기본은 IC 규칙으로 4분면, JM 은 2상태로
  "stress vs calm" 메타신호 → IC 라벨에 confidence 보정 + filter/smoother 발산 탐지(§5.8-H).
  4분면 직접 JM 학습은 라벨 매핑 모호 → 보수적으로 규칙 우선 + JM 보강.
"""
from __future__ import annotations

import logging
import time
from typing import Optional

import numpy as np
import pandas as pd

from .macro_schema import (
    Bloc,
    MacroView,
    RegimeEstimate,
    RegimeLabel,
    ViewStatus,
)
from . import macro_indicators as ind
from .fred_adapter import (
    FredAdapter,
    MacroFeatureBundle,
    NullFredAdapter,
    fetch_macro_bundle,
)
from . import indicator_event_correlation as iec

logger = logging.getLogger(__name__)


class RegimeClassifier:
    """
    결정론 거시 레짐 분류기. 매 사이클 호출 → MacroView baseline 생성 (C3 freshness).

    파이프라인:
      1) 피처 적재 (fetch_macro_bundle) — 실패 시 last-good stale / unavailable degrade (H29).
      2) Investment Clock 4분면 (성장 z × 인플레 z) → regime_now baseline.
      3) JM/SJM 2상태 stress 신호 → confidence 보정 + filter/smoother 발산 탐지 (§5.8-H).
      4) Michez/Sahm/금리커브/Truflation 으로 evidence 채우고 STAGFLATION/REFLATION 보정.
      5) 선행지표(금리커브·breakeven·payrolls 모멘텀) → regime_forecast (classifier 와 분리).
      6) per-bloc 반복 (USD; KRW 는 ECOS 미연동 시 USD 폴백).
    """

    def __init__(
        self,
        usd_adapter: Optional[FredAdapter] = None,
        krw_adapter: Optional[FredAdapter] = None,
        use_jump_model: bool = True,
        jump_penalty: float = 50.0,
        forecast_horizon_months: int = 6,
        correlation_model: Optional[iec.IndicatorEventCorrelation] = None,
    ):
        self.usd_adapter = usd_adapter or NullFredAdapter()
        self.krw_adapter = krw_adapter  # None → KRW=USD 폴백.
        self.use_jump_model = use_jump_model
        self.jump_penalty = jump_penalty
        self.forecast_horizon_months = forecast_horizon_months
        # §5.8-H 상관/오판 메모리 — 조건부 약화로 confidence 보수화 + caution 전파.
        self.correlation_model = correlation_model or iec.IndicatorEventCorrelation()

        self._last_good: Optional[MacroView] = None
        # JM 인스턴스 캐시 (bloc별) — 재학습 비용 절감.
        self._jm_cache: dict = {}

    # ------------------------------------------------------------------ 공개 API
    def classify(self, as_of: Optional[pd.Timestamp] = None) -> MacroView:
        """
        매 사이클 진입점. 모든 bloc 레짐을 추정해 MacroView 반환.
        portfolio_orchestrator → regime_to_weights 가 이 출력을 소비한다.
        """
        regimes = {}

        # USD bloc (메인).
        usd_bundle = self._safe_fetch(self.usd_adapter, as_of)
        usd_est = self._estimate_bloc(Bloc.USD, usd_bundle)

        if usd_est is None:
            # 데이터 전무 → last-good stale 재사용 (H29) 또는 unavailable.
            if self._last_good is not None:
                logger.warning("RegimeClassifier: USD data unavailable, degrade to last-good stale")
                return self._last_good.degrade_to_stale()
            logger.error("RegimeClassifier: no data and no last-good → unavailable")
            return MacroView.unavailable()
        regimes[Bloc.USD] = usd_est

        # KRW bloc — ECOS 어댑터 있으면 독립 추정, 없으면 USD 레짐 폴백.
        if self.krw_adapter is not None:
            krw_bundle = self._safe_fetch(self.krw_adapter, as_of)
            krw_est = self._estimate_bloc(Bloc.KRW, krw_bundle)
            regimes[Bloc.KRW] = krw_est if krw_est is not None else self._clone_as_bloc(usd_est, Bloc.KRW)
        else:
            regimes[Bloc.KRW] = self._clone_as_bloc(usd_est, Bloc.KRW)

        view = MacroView(
            regimes=regimes,
            status=ViewStatus.FRESH,
            as_of_ts=time.time(),
            data_as_of_ts=(usd_bundle.data_as_of.timestamp() if usd_bundle.data_as_of is not None else None),
            citation_ids=usd_est.citation_ids,
        )
        if view.is_well_formed():
            self._last_good = view
        return view

    # ------------------------------------------------------------ bloc 단위 추정
    def _estimate_bloc(self, bloc: Bloc, bundle: MacroFeatureBundle) -> Optional[RegimeEstimate]:
        if not bundle.available or not bundle.series:
            return None

        # --- (2) Investment Clock 성장 z × 인플레 z → regime_now ---
        growth_z = self._growth_signal(bundle)
        infl_z = self._inflation_signal(bundle)
        if growth_z is None or infl_z is None:
            return None
        regime_now, ic_conf = ind.investment_clock_quadrant(growth_z, infl_z)

        evidence = {"growth_z": round(growth_z, 3), "inflation_z": round(infl_z, 3)}
        citations = ["GDPC1", "CPILFESL", "PAYEMS"]

        # --- (4) 정량 법칙으로 evidence 보강 + 레짐 보정 ---
        regime_now, ic_conf = self._apply_indicator_overrides(
            bundle, regime_now, ic_conf, evidence, citations
        )

        # --- (3) JM/SJM 2상태 stress 신호 → confidence 보정 + 발산 탐지 (§5.8-H) ---
        jm_conf_adj, jm_evidence = self._jump_model_overlay(bloc, bundle)
        evidence.update(jm_evidence)
        confidence_now = float(np.clip(ic_conf * jm_conf_adj, 0.0, 1.0))

        # --- (3b) 조건부 상관 약화 (§5.8-H) — 보조지표가 임계 넘으면 baseline 상관 신뢰도 하향 ---
        confidence_now, corr_evidence = self._apply_correlation_attenuation(
            regime_now, bundle, evidence, confidence_now
        )
        evidence.update(corr_evidence)

        # --- (5) forecaster — 선행지표 기반 N개월 후 레짐 (classifier 와 분리) ---
        regime_fc, fc_conf = self._forecast_regime(bundle, regime_now, growth_z, infl_z)

        return RegimeEstimate(
            bloc=bloc,
            regime_now=regime_now,
            confidence_now=confidence_now,
            regime_forecast=regime_fc,
            forecast_horizon_months=self.forecast_horizon_months,
            confidence_forecast=fc_conf,
            method="ensemble" if self.use_jump_model else "investment_clock",
            evidence=evidence,
            citation_ids=citations,
        )

    # ------------------------------------------------------ 성장/인플레 신호 (z-score)
    def _growth_signal(self, b: MacroFeatureBundle) -> Optional[float]:
        """
        성장축: 실질GDP YoY + 비농업고용 모멘텀 + 산업생산 YoY 의 z-score 합성.
        macro.md(라인 110): payrolls(dlogPAYEMS) 가 침체예측 SHAP 1위 → 가중 우대.
        """
        signals, weights = [], []
        gdp = b.ts("real_gdp")
        if gdp is not None and len(gdp) >= 5:
            signals.append(_yoy_z(gdp, periods=4))   # 분기 → YoY = 4기.
            weights.append(1.0)
        pay = b.ts("nonfarm_payrolls")
        if pay is not None and len(pay) >= 13:
            signals.append(_momentum_z(pay, window=3))
            weights.append(1.5)   # SHAP 1위 가중.
        indpro = b.ts("industrial_production")
        if indpro is not None and len(indpro) >= 13:
            signals.append(_yoy_z(indpro, periods=12))
            weights.append(0.8)
        if not signals:
            return None
        return float(np.average(signals, weights=weights))

    def _inflation_signal(self, b: MacroFeatureBundle) -> Optional[float]:
        """
        물가축: 코어CPI YoY **레벨(목표 대비) + 모멘텀** 2D 합성 + breakeven(시장 선행).
        macro.md(라인 33~37): CPI vs PCE 괴리 → 둘 다 보고, breakeven 으로 기대 보강.

        ★M1(2026-06-02, 자문 gemini+claude 2R 수렴 + T0 2022 실측): momentum-only 는 가속이 멈춘
        지속 고물가 국면(2022 CPI 9.1% peak, yoy momentum≈0)을 "물가 낮음"으로 오독 → Recovery 오분류.
        Investment Clock 원형도 물가의 절대수준을 버리지 않음. level(목표 2% 대비 편차를 역사 변동성으로
        정규화) 을 주신호, momentum(전환점 선행) 을 보조로 결합. 자문 공식:
        w1·(yoy−target)/σ_level + w2·Δyoy/σ_mom. w1>w2 (level 주도, 지속성 포착).

        ★상수 calibration: target=2.0 / w_level=1.0 / w_mom=0.5 / w_bei=0.7 / window=36 은
        **자문 합의 기반 advisory prior, 백테스트 미캘리브레이션**(backtested=false). 독립 audit(2026-06-02,
        af651d4c) raw 재현 verdict=채택: 2022 복원 정당(core CPI 6.6% 실측), w_level 0.7~2.0 전부 2022 양
        유지=과적합 아님, PIT lookahead 0. minor: core PCE fallback 시 2.0 target 은 ~0.3%p 보수(CPI>PCE).
        """
        signals, weights = [], []
        core = b.ts("core_cpi")
        if core is None:
            core = b.ts("core_pce")
        if core is not None and len(core) >= 13:
            yoy = _yoy(core, 12).dropna()
            # level: 목표(2%) 대비 편차 = 지속 고물가 포착 (momentum miss 보완). 주신호.
            signals.append(_level_z(yoy, target=2.0, window=36))
            weights.append(1.0)
            # momentum: yoy 가속/감속 = 국면 전환점 선행. 보조.
            signals.append(_momentum_z(yoy, window=3))
            weights.append(0.5)
        bei = b.ts("breakeven_5y")
        if bei is not None and len(bei) >= 13:
            signals.append(_zscore(bei.diff(), window=12))
            weights.append(0.7)
        if not signals:
            return None
        return float(np.average(signals, weights=weights))

    # ------------------------------------------------ macro.md 법칙으로 레짐 보정
    def _apply_indicator_overrides(self, b, regime, conf, evidence, citations):
        """Michez/Sahm/금리커브/GDP-GDI/Truflation 으로 evidence 채우고 레짐 보정."""
        u = b.ts("unemployment_rate")
        v = b.ts("vacancy_rate")

        # Michez Rule — 침체 앵커 (macro.md 215). certain → STAGFLATION/REFLATION 쪽으로.
        if u is not None and v is not None:
            mz = ind.michez_rule(u, v)
            if mz is not None:
                evidence["michez_m"] = round(mz.m_value, 3)
                evidence["michez_state"] = mz.state
                evidence["michez_recession_prob"] = round(mz.recession_prob, 3)
                citations.append("UNRATE")
                if mz.state == "certain_recession":
                    # 확정 침체 = 성장 강한 음 → 인플레 따라 REFLATION/STAGFLATION.
                    infl = evidence.get("inflation_z", 0.0)
                    regime = RegimeLabel.STAGFLATION if infl > 0 else RegimeLabel.REFLATION
                    conf = max(conf, mz.recession_prob)

        # Sahm — 보조 교차검증 (공급충격 취약, macro.md 207).
        if u is not None:
            sahm = ind.sahm_rule(u)
            if sahm is not None:
                evidence["sahm_spread"] = round(sahm["sahm_spread"], 3)
                evidence["sahm_triggered"] = sahm["triggered"]
                # Sahm 트리거인데 Michez 미확정이면 = 공급충격 의심 → confidence 깎음(과민 차단).
                if sahm["triggered"] and evidence.get("michez_state") == "expansion":
                    conf *= 0.8
                    evidence["sahm_michez_divergence"] = True  # macro.md 핵심 통찰.

        # 금리커브 — 역전 무력화 / 스티프닝 구분 (macro.md 131~136).
        yc = b.ts("yield_10y_2y")
        if yc is not None:
            ycs = ind.yield_curve_signal(yc)
            if ycs is not None:
                evidence["yield_curve"] = ycs["regime_hint"]
                evidence["yc_spread"] = round(ycs["spread_now"], 3)
                citations.append("T10Y2Y")

        # GDP-GDI 크로스체크 — 기술적 침체 오경보 차단 (macro.md 151~156).
        gdp, gdi = b.ts("real_gdp"), b.ts("real_gdi")
        if gdp is not None and gdi is not None:
            gg = ind.gdp_gdi_divergence(_yoy(gdp, 4), _yoy(gdi, 4))
            if gg is not None and gg.get("divergence_warning"):
                evidence["gdp_gdi_divergence"] = True
                conf *= 0.85   # GDP만 보고 침체 단정 보류 → confidence 하향.

        return regime, conf

    # ----------------------------------------------------- JM/SJM overlay (§5.8-A)
    def _jump_model_overlay(self, bloc: Bloc, b: MacroFeatureBundle):
        """
        jumpmodels JM 2상태(calm/stress) 학습 → filter(실시간) vs smoother(사후) 발산이면
        오판 후보 (§5.8-H ⓑ). stress 상태면 IC confidence 하향. 미설치/실패 시 conf 보정 1.0.
        """
        if not self.use_jump_model:
            return 1.0, {}
        try:
            from jumpmodels.jump import JumpModel
            from jumpmodels.preprocess import StandardScalerPD, DataClipperStd
        except Exception:
            return 1.0, {"jm_status": "unavailable"}

        X, ret_proxy = self._build_jm_matrix(b)
        if X is None or len(X) < 60:
            return 1.0, {"jm_status": "insufficient_data"}

        try:
            scaler, clipper = StandardScalerPD(), DataClipperStd(mul=3.0)
            Xp = scaler.fit_transform(clipper.fit_transform(X))
            jm = JumpModel(n_components=2, jump_penalty=self.jump_penalty, cont=False)
            # ret_ser 로 상태 정렬: cumret 낮은 쪽 = stress(0), 높은 쪽 = calm(1).
            jm.fit(Xp, ret_ser=ret_proxy, sort_by="cumret")
            online_labels = jm.predict_online(Xp)        # filter (실시간).
            insample_labels = jm.labels_                  # smoother (사후).
            cur_state = int(online_labels.iloc[-1]) if hasattr(online_labels, "iloc") else int(online_labels[-1])

            # filter vs smoother 발산 (최근 6관측) → 오판 후보.
            try:
                tail_n = min(6, len(insample_labels))
                online_tail = np.asarray(online_labels)[-tail_n:]
                smoother_tail = np.asarray(insample_labels)[-tail_n:]
                divergence = float(np.mean(online_tail != smoother_tail))
            except Exception:
                divergence = 0.0

            evidence = {
                "jm_state": "calm" if cur_state == 1 else "stress",
                "jm_filter_smoother_divergence": round(divergence, 3),
                "jm_status": "ok",
            }
            # stress 상태 = IC confidence 하향(레짐 전환 불확실). 발산 크면 추가 하향.
            conf_adj = 1.0
            if cur_state == 0:
                conf_adj *= 0.85
            conf_adj *= (1.0 - 0.5 * divergence)
            return float(np.clip(conf_adj, 0.3, 1.0)), evidence
        except Exception as e:
            logger.debug("JM overlay failed: %s", e)
            return 1.0, {"jm_status": "error"}

    def _build_jm_matrix(self, b: MacroFeatureBundle):
        """
        JM 입력 행렬 X (월별 정렬 거시피처) + ret_proxy(상태정렬용 수익률 프록시).
        sparse JM 이 피처선택을 하므로 후보 피처를 넉넉히 넣는다 (§5.8-A SJM).
        """
        cols = {}
        # ★누락지표 보강: HY OAS(risk-regime, IG BAA10Y 보완) + real_rate_10y(M3 1차 driver, 방어적 macro state).
        # sparse JM feature-selection + len<60 graceful skip 으로 무회귀.
        # ⚠️Fisher: nominal_10y level 미포함(spread T10Y2Y + breakeven 만) → real_rate 추가해도 정확공선 아님.
        # ★비대칭 주의(main 감사): 활성 2종(HY OAS/real_rate)도 regime-분류 OOS hit 개선은 보류 2종과 *동일하게 미검증*.
        #   활성 근거 = (a)비-tautology(시장가격 아님→순환참조 無) + (b)factor-beta prior(M3 1차 driver)뿐,
        #   regime-IC OOS 아님. 보류 2종과의 유일한 차이 = tautology 안전 유무. (활성=검증완료 라는 인상 방지)
        # # 후보(OOS 검증 후 활성): "dollar_broad", "oil_wti" — 시장가격이라 regime 분류 tautology 위험
        # # (R1 FCI 경고 동형) + OOS 분류개선 미검증 → FRED 실데이터+regime-eval harness 확보 후 활성.
        # # ★B(a) regime-eval harness REJECTED(2026-05-31, study-research/macro/raw/validation-bgroup-2026-05-31.md):
        # #   forward 21d risk-off OOS Rank-IC 게이트 4/4 FAIL(dxy 부호반전 IS+0.075→OOS-0.056·전 신호 CI∋0)
        # #   + baseline(real,term,VIX) 증분 -0.095 악화 → tautology 데이터 입증 = 보류 확정(활성화 차단).
        # ★빈도 통일 fix(2026-06-02): 일/주/월 혼합 시리즈를 공통 월말(ME) 그리드로 정규화 후 변환.
        #   이전엔 월별 yoy(매월 1일 인덱스)·resample ME diff(월말)·breakeven 일별 yoy(diff_list 누락→일별)
        #   세 빈도가 섞여 DataFrame(cols).dropna() inner-join 교집합 ≈ 0 → X 0행 → *항상* insufficient_data
        #   (단발/시계열 무관). 모든 시리즈를 ME.last() 로 월말 통일 → 변환 후 정렬 일치.
        # 레벨 vs 변화율: 가격/스프레드/기대인플레(시장 level)는 diff, 거시지수는 YoY%.
        diff_names = ("yield_10y_2y", "nfci", "cfnai", "credit_spread_baa",
                      "credit_spread_hy_oas", "real_rate_10y", "breakeven_5y")
        for name in (*diff_names, "industrial_production", "core_cpi", "unemployment_rate"):
            s = b.ts(name)
            if s is None or len(s) < 60:
                continue
            m = s.resample("ME").last()                       # 공통 월말 그리드(빈도 통일)
            c = (m.diff() if name in diff_names else _yoy(m, 12)).dropna()
            if len(c) >= 60:                                  # 변환후 60mo 미확보(hy_oas 35mo 등) → 제외
                cols[name] = c
        if len(cols) < 3:
            return None, None
        X = pd.DataFrame(cols).dropna()
        if len(X) < 60:
            return None, None
        # ret_proxy: 신용스프레드 음의 변화 = 위험선호(상태정렬), 없으면 산업생산.
        if "credit_spread_baa" in X.columns:
            ret = -X["credit_spread_baa"]
        else:
            ret = X.iloc[:, 0]
        return X, ret

    # ------------------------------------------- 조건부 상관 약화 (§5.8-H, iec)
    def _apply_correlation_attenuation(self, regime, bundle, evidence, confidence):
        """
        indicator_event_correlation 으로 보조지표 trigger 시 confidence 를 동적 하향한다.
        예: RECESSION_ONSET 레짐인데 V/U 비율 높음(노동 타이트) → Sahm 오작동 케이스 발동 → conf↓.
        발동 케이스는 caution flag 로 evidence 에 기록(§5.8-H 메모리 + macro_reasoning 입력).
        """
        try:
            event = iec.infer_event_from_regime(regime)
            # 보조지표 실제값 수집 (FRED + 분류기 파생).
            extra = self._collect_supplementary(bundle)
            ind_values = iec.build_indicator_values(evidence, extra=extra)
            res = self.correlation_model.score_confidence(event, confidence, ind_values)
            new_conf = float(np.clip(confidence * res.confidence_multiplier, 0.1, 1.0))
            ev = {}
            if res.fired_cases:
                ev["corr_break_cases"] = res.fired_cases
                ev["corr_caution"] = res.caution_flags
                ev["corr_attenuation"] = round(res.confidence_multiplier, 3)
            return new_conf, ev
        except Exception as e:
            logger.debug("correlation attenuation skipped: %s", e)
            return confidence, {}

    def _collect_supplementary(self, b: MacroFeatureBundle) -> dict:
        """
        조건부 약화에 필요한 보조지표 현재값 수집 (배경문서 §2 의 sensing 지표).
        FRED 에 있으면 그 값, 파생은 계산. 없으면 생략(해당 케이스 미발동).
        """
        sup = {}
        # V/U 비율 = job_openings / unemployed (Sahm 오작동 sensing).
        jo, u = b.ts("job_openings"), b.ts("unemployment_rate")
        unemp = b.ts("labor_force")
        if jo is not None and unemp is not None and u is not None and len(jo) and len(unemp) and len(u):
            # 실업자수 근사 = labor_force * unemployment_rate/100.
            unemployed = float(unemp.iloc[-1]) * float(u.iloc[-1]) / 100.0
            if unemployed > 0:
                sup["vacancy_to_unemployed"] = float(jo.iloc[-1]) / unemployed
        # GDP-GDI: real_gdi 최신 YoY (음/양 분기 sensing).
        gdi = b.ts("real_gdi")
        if gdi is not None and len(gdi) >= 5:
            sup["real_gdi"] = float(_yoy(gdi, 4).iloc[-1])
        # michez_m 은 evidence 에서 이미 옴.
        return sup

    # ---------------------------------------------------------- forecaster (선행)
    def _forecast_regime(self, b, regime_now, growth_z, infl_z):
        """
        선행지표(금리커브 방향·breakeven·payrolls 모멘텀)로 N개월 후 레짐 추정.
        classifier(현재)와 *반드시 분리* (§5.8-A). 선행 신호가 현재와 같으면 동일, 다르면 전환 예고.
        """
        yc = b.ts("yield_10y_2y")
        lead_growth = growth_z
        lead_infl = infl_z

        # 금리커브 스티프닝(bull) = 성장 회복 선행 신호.
        if yc is not None and len(yc) >= 60:
            ycs = ind.yield_curve_signal(yc)
            if ycs is not None:
                if ycs["regime_hint"] == "steepening_recovery":
                    lead_growth += 0.3
                elif ycs["regime_hint"] == "inverted_caution":
                    lead_growth -= 0.3

        # breakeven 상승 = 인플레 선행.
        bei = b.ts("breakeven_5y")
        if bei is not None and len(bei) >= 4:
            slope = float(bei.diff().tail(3).mean())
            lead_infl += np.sign(slope) * min(abs(slope), 0.3)

        regime_fc, fc_conf = ind.investment_clock_quadrant(lead_growth, lead_infl)
        # forecaster 는 본질적으로 더 불확실 → confidence 보수적 캡.
        return regime_fc, float(min(fc_conf, 0.6))

    # ----------------------------------------------------------------- helpers
    def _safe_fetch(self, adapter: FredAdapter, as_of) -> MacroFeatureBundle:
        try:
            return fetch_macro_bundle(adapter, as_of=as_of)
        except Exception as e:  # C2: source_missing 라벨 — 동작 동일(available=False), silent 제거
            logger.warning(
                "fetch_macro_bundle source_missing [label=source_missing]: %s", e
            )
            return MacroFeatureBundle(available=False)

    @staticmethod
    def _clone_as_bloc(est: RegimeEstimate, bloc: Bloc) -> RegimeEstimate:
        """KRW 데이터 없을 때 USD 레짐을 폴백 복제 (낮춘 confidence + 폴백 마킹)."""
        import copy
        c = copy.deepcopy(est)
        c.bloc = bloc
        c.confidence_now *= 0.7
        c.method = est.method + "_usd_fallback"
        c.evidence = dict(c.evidence, krw_fallback=True)
        return c


# ===========================================================================
# z-score / YoY / 모멘텀 유틸 (PIT-safe; rolling 만 사용 — 미래 미참조)
# ===========================================================================
def _yoy(s: pd.Series, periods: int) -> pd.Series:
    return (s / s.shift(periods) - 1.0) * 100.0


def _zscore(s: pd.Series, window: int = 36) -> float:
    s = s.dropna()
    if len(s) < max(window // 2, 4):
        return 0.0
    tail = s.tail(window)
    mu, sd = tail.mean(), tail.std()
    if sd == 0 or pd.isna(sd):
        return 0.0
    return float((s.iloc[-1] - mu) / sd)


def _yoy_z(s: pd.Series, periods: int, window: int = 36) -> float:
    return _zscore(_yoy(s, periods).dropna(), window)


def _level_z(s: pd.Series, target: float = 0.0, window: int = 36) -> float:
    """목표(target) 대비 현재 레벨 편차를 rolling 변동성으로 정규화 (PIT-safe, 미래 미참조).

    ★M1: _zscore 는 자체 평균 대비(상대 위치)라 안정 평균이 따라 올라가면 지속 고물가를 못 잡음.
    target anchor(물가=목표 2%) 대비 편차를 σ 로 정규화 → 절대 수준이 목표를 벗어날수록 큰 신호.
    """
    s = s.dropna()
    if len(s) < max(window // 2, 4):
        return 0.0
    sd = s.tail(window).std()
    if sd == 0 or pd.isna(sd):
        return 0.0
    return float((s.iloc[-1] - target) / sd)


def _momentum_z(s: pd.Series, window: int = 3, z_window: int = 36) -> float:
    mom = s.pct_change(window) * 100.0
    return _zscore(mom.dropna(), z_window)


def _is_high_freq(s: pd.Series) -> bool:
    if len(s) < 3:
        return False
    median_days = pd.Series(s.index).diff().dt.days.median()
    return bool(median_days is not None and median_days < 25)
