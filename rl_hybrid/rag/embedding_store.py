"""벡터 임베딩 저장소 — core.db 어댑터 기반

rag_analysis_vectors 테이블에 Gemini 분석 임베딩을 저장하고,
코사인 유사도 검색(rpc_match)을 수행한다.
core.db 어댑터(INV_DB_BACKEND=sqlite 기본) 경유 — 백엔드 무관.
임베딩은 raw float list 그대로 전달 (어댑터가 백엔드별 직렬화).
"""

import logging
import os
import sys
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from core.db import db
from rl_hybrid.config import config

logger = logging.getLogger("rag.embedding_store")


class EmbeddingStore:
    """core.db 어댑터 기반 임베딩 CRUD"""

    def __init__(self):
        # core.db 어댑터가 백엔드를 관리 — URL/키 불필요.
        pass

    def store_analysis(
        self,
        cycle_id: str,
        analysis_text: str,
        analysis_json: dict,
        embedding: list[float],
        market_regime: str = None,
        decision_id: str = None,
    ) -> Optional[str]:
        """분석 결과 + 임베딩 저장

        Returns:
            생성된 레코드 UUID, 실패 시 None
        """
        try:
            payload = {
                "cycle_id": cycle_id,
                "analysis_text": analysis_text,
                "analysis_json": analysis_json,
                "market_regime": market_regime or analysis_json.get("market_regime"),
                "embedding": embedding,  # raw list (어댑터가 백엔드별 직렬화)
            }
            if decision_id:
                payload["decision_id"] = decision_id

            row = db.insert("rag_analysis_vectors", payload)
            record_id = row.get("id") if row else None
            logger.info(f"임베딩 저장 완료: id={record_id}, cycle={cycle_id}")
            return record_id

        except Exception as e:
            logger.error(f"임베딩 저장 실패: {e}")
            return None

    def search_similar(
        self,
        query_embedding: list[float],
        top_k: int = None,
        threshold: float = None,
    ) -> list[dict]:
        """코사인 유사도 검색 (rpc_match)

        Returns:
            [{"id", "cycle_id", "analysis_text", "analysis_json",
              "market_regime", "similarity", "created_at"}, ...]
        """
        top_k = top_k or config.rag.top_k
        threshold = threshold or config.rag.similarity_threshold

        try:
            rows = db.rpc_match(
                "rag_analysis_vectors", query_embedding,
                column="embedding", k=top_k,
            )
            results = []
            for r in rows:
                sim = r.pop("_similarity", None)
                if sim is not None:
                    if sim < threshold:
                        continue
                    r["similarity"] = sim
                results.append(r)
            logger.info(f"유사 분석 검색: {len(results)}건 (threshold={threshold})")
            return results

        except Exception as e:
            logger.error(f"유사 분석 검색 실패: {e}")
            return []

    def get_recent_analyses(self, limit: int = 10) -> list[dict]:
        """최근 분석 조회 (RAG 컨텍스트 구성용)"""
        try:
            return db.select(
                "rag_analysis_vectors",
                select="cycle_id,analysis_text,analysis_json,market_regime,created_at",
                order="created_at.desc",
                limit=limit,
            )
        except Exception as e:
            logger.error(f"최근 분석 조회 실패: {e}")
            return []
