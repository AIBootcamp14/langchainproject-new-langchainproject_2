"""
CRUD 유틸리티 함수
"""
from sqlalchemy.orm import Session
from sqlalchemy import text, desc
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import logging

from app.db.models import (
    Session as ChatSession,
    Message,
    LawParamSnapshot,
    DartCache,
    CalcResult,
    RagDoc,
    generate_uuid
)

logger = logging.getLogger(__name__)


# ==================== Session ====================

def create_session(db: Session) -> ChatSession:
    """새 채팅 세션 생성"""
    session = ChatSession(id=generate_uuid())
    db.add(session)
    db.commit()
    db.refresh(session)
    logger.info(f"새 세션 생성: {session.id}")
    return session


def get_session(db: Session, session_id: str) -> Optional[ChatSession]:
    """세션 조회"""
    return db.query(ChatSession).filter(ChatSession.id == session_id).first()


# ==================== Message ====================

def append_message(db: Session, session_id: str, role: str, content: str) -> Message:
    """메시지 추가"""
    message = Message(
        id=generate_uuid(),
        session_id=session_id,
        role=role,
        content=content
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def get_messages_by_session(db: Session, session_id: str) -> List[Message]:
    """세션의 모든 메시지 조회 (시간순)"""
    return db.query(Message).filter(
        Message.session_id == session_id
    ).order_by(Message.created_at).all()


# ==================== LawParamSnapshot ====================

def save_law_param_snapshot(db: Session, version: str, params: Dict[str, Any]) -> LawParamSnapshot:
    """법령 파라미터 스냅샷 저장"""
    # 기존 버전 확인
    existing = db.query(LawParamSnapshot).filter(
        LawParamSnapshot.version == version
    ).first()

    if existing:
        logger.info(f"법령 파라미터 버전 {version}이 이미 존재합니다")
        return existing

    snapshot = LawParamSnapshot(
        id=generate_uuid(),
        version=version,
        json_blob=params
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    logger.info(f"법령 파라미터 스냅샷 저장: {version}")
    return snapshot


def get_latest_law_param_snapshot(db: Session) -> Optional[LawParamSnapshot]:
    """최신 법령 파라미터 스냅샷 조회"""
    return db.query(LawParamSnapshot).order_by(
        desc(LawParamSnapshot.created_at)
    ).first()


def get_law_param_snapshot_by_version(db: Session, version: str) -> Optional[LawParamSnapshot]:
    """특정 버전 법령 파라미터 조회"""
    return db.query(LawParamSnapshot).filter(
        LawParamSnapshot.version == version
    ).first()


# ==================== DartCache ====================

def save_dart_cache(
    db: Session,
    corp_name: Optional[str],
    corp_code: Optional[str],
    period: Optional[str],
    key: str,
    value: str,
    raw_source: Optional[str] = None
) -> DartCache:
    """DART API 응답 캐시 저장"""
    cache = DartCache(
        id=generate_uuid(),
        corp_name=corp_name,
        corp_code=corp_code,
        period=period,
        key=key,
        value=value,
        raw_source=raw_source
    )
    db.add(cache)
    db.commit()
    db.refresh(cache)
    return cache


def get_dart_cache(
    db: Session,
    corp_code: Optional[str],
    key: str,
    period: Optional[str] = None
) -> Optional[DartCache]:
    """DART 캐시 조회"""
    query = db.query(DartCache).filter(DartCache.key == key)

    if corp_code:
        query = query.filter(DartCache.corp_code == corp_code)

    if period:
        query = query.filter(DartCache.period == period)

    return query.order_by(desc(DartCache.fetched_at)).first()


# ==================== CalcResult ====================

def save_calc_result(
    db: Session,
    session_id: str,
    corp_name: str,
    corp_code: Optional[str],
    law_param_version: str,
    result_json: Dict[str, Any],
    summary_text: Optional[str] = None,
    pdf_path: Optional[str] = None
) -> CalcResult:
    """법인세 계산 결과 저장"""
    result = CalcResult(
        id=generate_uuid(),
        session_id=session_id,
        corp_name=corp_name,
        corp_code=corp_code,
        calc_date=datetime.utcnow(),
        law_param_version=law_param_version,
        result_json=result_json,
        summary_text=summary_text,
        pdf_path=pdf_path
    )
    db.add(result)
    db.commit()
    db.refresh(result)
    logger.info(f"계산 결과 저장: {result.id} (기업: {corp_name})")
    return result


def get_calc_results_by_corp(db: Session, corp_name: str, limit: int = 10) -> List[CalcResult]:
    """특정 기업의 계산 결과 조회"""
    return db.query(CalcResult).filter(
        CalcResult.corp_name == corp_name
    ).order_by(desc(CalcResult.calc_date)).limit(limit).all()


def get_calc_result_by_id(db: Session, result_id: str) -> Optional[CalcResult]:
    """특정 계산 결과 조회"""
    return db.query(CalcResult).filter(CalcResult.id == result_id).first()


# ==================== RagDoc ====================

def upsert_rag_doc(
    db: Session,
    doc_type: str,
    title: str,
    content: str,
    meta_json: Optional[Dict[str, Any]] = None
) -> RagDoc:
    """RAG 문서 저장 (FTS5 색인 포함)"""
    doc = RagDoc(
        id=generate_uuid(),
        doc_type=doc_type,
        title=title,
        content=content,
        meta_json=meta_json or {}
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # FTS5 테이블에 색인
    try:
        db.execute(text(
            "INSERT INTO rag_fts (doc_id, title, content) VALUES (:doc_id, :title, :content)"
        ), {"doc_id": doc.id, "title": title, "content": content})
        db.commit()
        logger.info(f"RAG 문서 및 FTS5 색인 저장: {doc.id}")
    except Exception as e:
        logger.error(f"FTS5 색인 저장 실패: {e}")
        # FTS5 실패해도 문서는 저장됨

    return doc


def search_rag_fts(db: Session, query: str, k: int = 5) -> List[RagDoc]:
    """FTS5 기반 RAG 검색"""
    try:
        # FTS5로 검색
        result = db.execute(text(
            """
            SELECT doc_id FROM rag_fts
            WHERE rag_fts MATCH :query
            ORDER BY rank
            LIMIT :k
            """
        ), {"query": query, "k": k})

        doc_ids = [row[0] for row in result.fetchall()]

        if not doc_ids:
            logger.info(f"FTS5 검색 결과 없음: {query}")
            return []

        # doc_id로 실제 문서 조회
        docs = db.query(RagDoc).filter(RagDoc.id.in_(doc_ids)).all()
        logger.info(f"FTS5 검색 완료: {len(docs)}개 문서 반환")
        return docs

    except Exception as e:
        logger.error(f"FTS5 검색 실패: {e}")
        # 폴백: 단순 LIKE 검색
        logger.info("폴백: 단순 LIKE 검색 사용")
        return db.query(RagDoc).filter(
            RagDoc.content.like(f"%{query}%")
        ).limit(k).all()
