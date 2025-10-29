"""
데이터베이스 모델 정의
SQLAlchemy를 사용한 SQLite 테이블 정의
"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON, Integer, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()


def generate_uuid():
    """UUID 생성 헬퍼"""
    return str(uuid.uuid4())


class Session(Base):
    """채팅 세션 테이블"""
    __tablename__ = 'sessions'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 관계 정의
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")
    calc_results = relationship("CalcResult", back_populates="session", cascade="all, delete-orphan")


class Message(Base):
    """채팅 메시지 테이블 (멀티턴 히스토리)"""
    __tablename__ = 'messages'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), ForeignKey('sessions.id'), nullable=False)
    role = Column(String(20), nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 관계 정의
    session = relationship("Session", back_populates="messages")


class LawParamSnapshot(Base):
    """법령 파라미터 스냅샷 테이블"""
    __tablename__ = 'law_param_snapshots'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    version = Column(String(50), nullable=False, unique=True)
    json_blob = Column(JSON, nullable=False)  # 전체 법령 파라미터 JSON
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class DartCache(Base):
    """DART API 응답 캐시 테이블"""
    __tablename__ = 'dart_cache'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    corp_name = Column(String(200), nullable=True)
    corp_code = Column(String(20), nullable=True)
    period = Column(String(20), nullable=True)  # 예: '2023Q3'
    key = Column(String(100), nullable=False)  # 캐시 키 (예: 'corp_code', 'financials')
    value = Column(Text, nullable=True)  # JSON 문자열
    raw_source = Column(Text, nullable=True)  # 원본 응답
    fetched_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class CalcResult(Base):
    """법인세 계산 결과 테이블"""
    __tablename__ = 'calc_results'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), ForeignKey('sessions.id'), nullable=False)
    corp_name = Column(String(200), nullable=False)
    corp_code = Column(String(20), nullable=True)
    calc_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    law_param_version = Column(String(50), nullable=False)
    result_json = Column(JSON, nullable=False)  # 계산 상세 결과
    summary_text = Column(Text, nullable=True)  # 요약 텍스트
    pdf_path = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 관계 정의
    session = relationship("Session", back_populates="calc_results")


class RagDoc(Base):
    """RAG 문서 저장 테이블"""
    __tablename__ = 'rag_docs'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    doc_type = Column(String(50), nullable=False)  # 'calc_result', 'law_param', etc.
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)  # 검색 대상 텍스트
    meta_json = Column(JSON, nullable=True)  # corp_code, calc_date, law_version 등
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


# FTS5 가상 테이블은 raw SQL로 생성 (session.py에서 처리)
# CREATE VIRTUAL TABLE rag_fts USING fts5(doc_id, title, content)
