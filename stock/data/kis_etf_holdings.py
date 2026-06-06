"""stock/data/kis_etf_holdings.py — KIS Open API ETF 구성종목(PDF) 실 fetch (Phase 1-3 holdings).

WHY: pykrx ETF 구성종목은 KRX 로그인 차단(빈 응답). 한국투자증권 KIS Open API 는 credential
     (.env KIS_APPKEY/SECRET) 로 ETF 구성종목 시세를 직접 조회 가능 → look-through underlying 확정.

KIS endpoint: /uapi/etfetn/v1/quotations/inquire-component-stock-price (tr_id FHKST121600C0).
토큰: /oauth2/tokenP 발급(1분 1회 제한) → .kis-token-cache.json 캐싱(24h 유효) 재사용.

⛔ credential 절대 미노출(코드 내부만). 토큰 캐시 파일 = gitignore. 네트워크/credential 부재 → graceful 빈 결과.
⛔ 시세 조회는 실전 도메인만(모의 vts 미지원) — 주문 아님(읽기 전용, go-live 무관).
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger("stock.data.kis_etf_holdings")

_ROOT = Path(__file__).resolve().parents[2]
_TOKEN_CACHE = _ROOT / ".kis-token-cache.json"
_REAL_DOMAIN = "https://openapi.koreainvestment.com:9443"


@dataclass(frozen=True)
class KisEtfHolding:
    ticker: str
    name: str
    weight: float        # 구성비중(%)


def _load_env(path: Optional[Path] = None) -> dict:
    p = path or (_ROOT / ".env")
    d: dict = {}
    if not p.exists():
        return d
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            d[k.strip()] = v.strip().strip('"').strip("'")
    return d


def _get_token(ak: str, sk: str) -> Optional[str]:
    """토큰 캐시(24h) 재사용, 없거나 만료면 발급(1분 1회 제한). 실패 None(graceful)."""
    now = time.time()
    if _TOKEN_CACHE.exists():
        try:
            c = json.loads(_TOKEN_CACHE.read_text(encoding="utf-8"))
            if c.get("expires_at", 0) > now + 60 and c.get("access_token"):
                return c["access_token"]
        except Exception:
            pass
    try:
        import requests
        r = requests.post(_REAL_DOMAIN + "/oauth2/tokenP",
                          json={"grant_type": "client_credentials", "appkey": ak, "appsecret": sk},
                          timeout=15)
        if r.status_code != 200:
            logger.info("KIS 토큰 발급 실패 %s: %s", r.status_code, r.text[:120])
            return None
        j = r.json()
        tok = j.get("access_token")
        if not tok:
            return None
        # expires_in 초(보통 86400). 보수적으로 -300s.
        exp = now + float(j.get("expires_in", 86400)) - 300
        _TOKEN_CACHE.write_text(json.dumps({"access_token": tok, "expires_at": exp}), encoding="utf-8")
        return tok
    except Exception as exc:
        logger.info("KIS 토큰 graceful 실패: %s", exc)
        return None


def fetch_etf_holdings(etf_ticker: str, *, debug: bool = False) -> list[KisEtfHolding]:
    """KIS ETF 구성종목 조회 → [KisEtfHolding]. credential/네트워크 부재 → 빈 리스트(graceful)."""
    e = _load_env()
    ak, sk = e.get("KIS_APPKEY", ""), e.get("KIS_APPSECRET", "")
    if not (ak and sk):
        logger.info("KIS credential 부재 — ETF holdings 이연")
        return []
    tok = _get_token(ak, sk)
    if not tok:
        return []
    try:
        import requests
        h = {"authorization": f"Bearer {tok}", "appkey": ak, "appsecret": sk,
             "tr_id": "FHKST121600C0", "custtype": "P"}
        p = {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": etf_ticker,
             "FID_COND_SCR_DIV_CODE": "11216"}
        r = requests.get(_REAL_DOMAIN + "/uapi/etfetn/v1/quotations/inquire-component-stock-price",
                        headers=h, params=p, timeout=15)
        j = r.json()
        if debug:
            logger.warning("KIS resp keys=%s rt_cd=%s msg=%s", list(j.keys()), j.get("rt_cd"), j.get("msg1"))
            for k in j:
                if isinstance(j[k], list) and j[k]:
                    logger.warning("  %s[%d] keys=%s", k, len(j[k]), list(j[k][0].keys()))
        out = j.get("output2") or []
        holdings: list[KisEtfHolding] = []
        for it in out:
            cd = (it.get("stck_shrn_iscd") or it.get("mksc_shrn_iscd") or "").strip()
            nm = (it.get("hts_kor_isnm") or it.get("prdt_name") or "").strip()
            wt_raw = (it.get("etf_cnfg_issu_rlim") or it.get("cnfg_issu_rlim")
                      or it.get("issu_rlim") or "0")
            try:
                wt = float(str(wt_raw).replace(",", "") or 0)
            except ValueError:
                wt = 0.0
            if cd:
                holdings.append(KisEtfHolding(ticker=cd, name=nm, weight=wt))
        return holdings
    except Exception as exc:
        logger.info("KIS ETF holdings graceful 실패 %s: %s", etf_ticker, exc)
        return []


if __name__ == "__main__":
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    logging.basicConfig(level=logging.WARNING, format="%(message)s")

    tk = sys.argv[1] if len(sys.argv) > 1 else "244580"
    print(f"=== KIS ETF 구성종목 조회: {tk} ===")
    hs = fetch_etf_holdings(tk, debug=True)
    print(f"구성종목 {len(hs)}건")
    for h in hs[:15]:
        print(f"  {h.ticker} {h.name} 비중={h.weight}%")
