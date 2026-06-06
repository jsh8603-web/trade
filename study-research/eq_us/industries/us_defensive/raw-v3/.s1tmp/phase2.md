# US Defensive Equity — Phase 2 deep-dive: measurement & EDGAR data accessibility

Context: building cross-sectional stock-selection model for US defensive sleeve (consumer staples, utilities, healthcare, mature telecom). I already have Phase 1 (signals: low-vol/BAB, quality/gross-profitability, payout/shareholder yield, PER/value, earnings-stability/accruals, rate-duration, short-term reversal, credit-regime). Now I need PRECISE measurement & data-construction details from SEC EDGAR XBRL companyconcept API + yfinance + FRED.

## A. Payout / Shareholder Yield construction from EDGAR
- Boudoukh-Michaely-Richardson-Roberts 2007: payout yield = (dividends + net repurchases)/market cap. What are the exact SEC EDGAR us-gaap XBRL concept tags for: dividends paid (cash flow statement), common stock repurchased, common stock issued? List the standard concept names (e.g., PaymentsOfDividendsCommonStock, PaymentsForRepurchaseOfCommonStock, ProceedsFromIssuanceOfCommonStock).
- Is dividend yield ALONE (PaymentsOfDividends / mktcap) a weaker but cleaner signal than full shareholder yield? Defensive utilities rarely buy back stock; staples/healthcare do. 
- Sign expectation and crowding: is the dividend-yield anomaly mostly dead post-2015 (crowded into low-vol/quality ETFs)? Give decay magnitude if known.

## B. Earnings stability signal — how to measure cross-sectionally
- How is "earnings stability" operationalized as a tradeable factor? e.g., std-dev of trailing 5y EPS/ROE, or coefficient of variation of net income, or earnings persistence (AR1 coefficient). Which works best?
- Is there academic evidence that LOW earnings volatility predicts HIGHER forward returns within defensive/large-cap universe (separate from low-vol of returns)? Cite.

## C. PER vs Earnings Yield (E/P) for stable-earnings stocks — negative earnings handling
- For defensive stocks PER value premium should work (stable EPS). But how to handle the cross-sectional z-score when some firms have negative/near-zero earnings (e.g., a healthcare firm in a bad year)? Best practice: E/P (earnings yield, can be negative, monotone) vs P/E (undefined at E=0)? 
- Confirm: for asset-stable archetype, the BEST valuation metric ranked. Is PER better than PBR here (opposite of cyclicals where PBR>PER)? Or is FCF-yield / EV-EBITDA superior?

## D. Rate-duration cross-sectional signal — implementation
- To turn "rate sensitivity" into a cross-sectional signal: estimate each stock's rolling beta to changes in DFII10 (real 10y) or DGS10, then rank. But is the SIGN tradeable unconditionally, or only conditional on a rate-direction view? 
- Gormsen-Lazarus 2023 "Duration-Driven Returns": does long-high-duration earn an UNCONDITIONAL premium, or is it a risk factor with regime-dependent sign? For my unconditional cross-sectional IC test, will rate-beta show ~zero unconditional IC (pure risk factor)?

## E. Which defensive signals are most likely to SURVIVE multiple-testing (BY-FDR) in a small panel?
- I have a ~49-stock universe (15 staples, 15 utilities, 15 healthcare, 4 telecom), ~180 months (2010-2026). After Benjamini-Yekutieli FDR correction across ~16-36 tests, which 1-2 signals have the strongest priors to survive? Rank by expected robustness: low-vol, quality/gross-profitability, payout-yield, PER/value, earnings-stability, short-term-reversal.
- Important: sector-neutral (within-sub-sector demean) vs universe-demean — for a multi-sector defensive sleeve, does within-sector standardization matter? E.g., utilities all have high dividend yield vs healthcare — universe-demean would just pick "utilities vs healthcare" rather than within-sector value. Confirm sector-neutral z is the right approach.

## F. Sub-sector heterogeneity
- Do these signals have CONSISTENT sign across staples/utilities/healthcare/telecom, or does any sub-sector flip? e.g., dividend yield value in utilities (regulated) vs healthcare (growth-tilted). Where might cross-sectional sign cancel between sub-sectors?

Please cite precisely (author, year, journal, volume). Flag uncertain citations as [tentative]. Be concrete about EDGAR concept tag names.
