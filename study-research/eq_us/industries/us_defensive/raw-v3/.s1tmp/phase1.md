# US Defensive Equity Sector — Cross-Sectional Alpha Signal Literature Research (Phase 1, broad)

I am building a cross-sectional stock-selection model for a US DEFENSIVE equity sleeve composed of 4 sub-sectors:
- Consumer Staples (XLP): PG, KO, PEP, COST, WMT, PM, MO, CL, etc.
- Utilities (XLU): NEE, DUK, SO, D, AEP, etc.
- Healthcare (XLV): JNJ, UNH, LLY, MRK, ABBV, PFE, etc.
- Mature Communications (XLC-mature): VZ, T, CMCSA, TMUS

Archetype = "asset_stable" (stable cash flow, dividend, bond-proxy duration sensitivity). This is the DEFENSIVE counterpart to cyclicals.

## What I need (academic + practitioner literature, with PRECISE citations)

For each candidate cross-sectional signal that predicts forward returns WITHIN a universe of defensive large-cap stocks, give me:
1. Exact citation (author, year, journal, volume, title) — I will verify against hallucination.
2. Mechanism specific to DEFENSIVE / low-beta / bond-proxy equities.
3. Sign of the cross-sectional IC (does high or low value predict higher forward return).
4. Whether it is data-accessible from SEC EDGAR XBRL fundamentals + yfinance prices + FRED macro (no paid IBES/FactSet).

## Specific candidate signals to research (find the seminal papers + decay evidence):

1. **Low-volatility / low-beta anomaly (BAB)** — Frazzini-Pedersen, Baker-Bradley-Wurgler, Ang-Hodrick-Xing-Zhang. Is the low-vol premium concentrated in defensive sectors? Sign, mechanism (leverage constraints, lottery preference).

2. **Quality (QMJ) / gross profitability** — Asness-Frazzini-Pedersen "Quality Minus Junk", Novy-Marx gross profitability. Do defensive stocks (stable margins) reward quality differently than cyclicals?

3. **Dividend yield / payout yield / shareholder yield** — Boudoukh-Michaely-Richardson-Roberts (payout yield > dividend yield), dividend yield anomaly. Defensive sectors are dividend-heavy. Is dividend/payout yield a cross-sectional alpha here? Sign, crowding/decay.

4. **Valuation (PER, PBR, EV/EBITDA, earnings yield)** — for asset_stable archetype, does PER VALUE PREMIUM work (unlike cyclicals where peak-EPS trap breaks PER)? Defensive stocks have STABLE EPS, so PER should be a valid value metric. Confirm or refute this hypothesis with literature. Which valuation metric is best for stable-earnings stocks?

5. **Earnings stability / earnings quality / accruals** — Sloan accruals, earnings smoothness. Do stable-earnings defensive stocks have a tradeable earnings-stability premium?

6. **Rate / duration sensitivity (bond-proxy)** — defensive stocks (utilities, staples) behave like bonds (long duration). Literature on equity duration (Dechow-Sloan-Soliman, Weber, Gormsen-Lazarus "Duration-Driven Returns"), interest-rate beta as a cross-sectional risk factor. Real rate (DFII10) sensitivity.

7. **Short-term reversal** — Jegadeesh 1-month reversal. Is it stronger in defensive/low-vol stocks?

8. **Credit regime conditioning (HY OAS / Baa-Aaa default spread)** — Fama-French default spread. In risk-off (credit stress) regimes, do defensive stocks outperform? Regime conditioner, not cross-sectional.

9. **Defensive-specific factors** — anything specific to utilities (regulated returns, rate base growth), healthcare (patent cliffs, pipeline), staples (brand moat, pricing power), telecom (subscriber/ARPU). Are there sector-specific fundamental signals?

## Key hypothesis to test against literature:
- CYCLICALS suffer "peak-EPS trap" (PER fails, PBR/EV-EBITDA work). DEFENSIVES have STABLE earnings → PER value should work normally. Is this supported? This is the OPPOSITE of cyclicals.
- Are defensive-sector premia (low-vol, quality, dividend) subject to heavy post-2015 crowding/decay (McLean-Pontiff)?

Please be thorough and cite precisely. Flag any citation you are uncertain about as [tentative].
