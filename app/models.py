# app/models.py
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, ForeignKey, DateTime, Text, UniqueConstraint
# 쿼리문의 JOIN 을 대신함. 간결하게 (user.interests 처럼)
from sqlalchemy.orm import relationship
# 데이터베이스 자체 함수를 쓰고 싶을 때 사용
from sqlalchemy.sql import func
# database.py 에서 Base = declarative_base()
from app.database import Base

# 1. 회원 정보 (Users)
# database.py의 Base 를 상속받음 -> DB 테이블 모델임을 알 수 있음
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    nickname = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # user의 포트폴리오 연결
    portfolios = relationship("Portfolio", back_populates="owner")

    # 관계 설정 (User <-> UserInterest)
    # [수정] cascade옵션을 줘서 유저가 삭제되면 관심사도 같이 삭제되게 함
    interests = relationship("UserInterest", back_populates="user", cascade="all, delete-orphan")

# 2. 자산 마스터 (Assets)
# database.py의 Base 를 상속받음 -> DB 테이블 모델임을 알 수 있음
class Asset(Base):
    __tablename__ = "assets"

    code = Column(String, primary_key=True, index=True) # '005930', 'USD' 등
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    market = Column(String)

# 3. 사용자 관심 종목 (UserInterests)
# database.py의 Base 를 상속받음 -> DB 테이블 모델임을 알 수 있음
class UserInterest(Base):
    __tablename__ = "user_interests"

    id = Column(Integer, primary_key=True, index=True)

    # 자신(Asset) 테이블과 연결을 끊음. 그냥 문자열(ticker)로 지정
    ticker = Column(String, index=True, nullable=False)
    category = Column(String, default="stock") # 환율/주식 구분용

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 관계 설정 (역참조)
    user = relationship("User", back_populates="interests")

    # 유니크 제약조건 (파이썬 레벨에서도 명시)
    __table_args__ = (
        UniqueConstraint('user_id', 'ticker', name='uix_user_ticker'),
    )

# 4. 일일 브리핑 (DailyBriefings)
# database.py의 Base 를 상속받음 -> DB 테이블 모델임을 알 수 있음
class DailyBriefing(Base):
    __tablename__ = "daily_briefings"

    id = Column(Integer, primary_key=True, index=True)
    asset_code = Column(String, ForeignKey("assets.code", ondelete="CASCADE"))
    summary_text = Column(Text, nullable=False)
    news_links = Column(Text)
    # func.now() : DB서버(PostgreSQL)에게 데이터가 저장되는 순간을 찍으라 말하는 것
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    asset = relationship("Asset")

# 5. 포트폴리오
class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    
    ticker = Column(String, index=True) # 종목 코드 (예: VOO, 005930.KS)
    avg_price = Column(Float)           # 평균 단가
    quantity = Column(Float)            # 보유 주수 (소수점 거래 가능성을 위해 Float)
    
    owner = relationship("User", back_populates="portfolios")