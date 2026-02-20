# app/schemas.py
# BaseModel: pydantic의 핵심. 만드는 모든 스키마가 상속받음
# EmailStr: 이메일 형식 검사
from pydantic import BaseModel, EmailStr
from typing import Optional, List
# 날짜 다루기
from datetime import datetime

# --- 회원가입/로그인 할 때 사용자가 보내는 데이터 ---
class UserCreate(BaseModel):
    email: EmailStr  # 이메일 형식이 아니면 에러 냄
    password: str
    nickname: Optional[str] = None

# --- 사용자에게 보여줄 데이터 (비밀번호는 빼고 보여줌) ---
class UserResponse(BaseModel):
    id: int
    email: EmailStr
    nickname: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True  # ORM 객체를 Pydantic 모델로 변환 허용

# --- 관심 종목 추가할 때 받는 데이터 ---
class InterestCreate(BaseModel):
    asset_code: str

# -- 로그인 성공 시 발급해줄 토큰 양식 --
# 서버가 발급해 줌
class Token(BaseModel):
    access_token: str
    token_type: str
    nickname: str = "사용자"

# --- 주식/환율 정보 포장지 ---
class PriceResponse(BaseModel):
    code: str
    price: float
    change_percent: float
    currency: str

# --- 뉴스 정보 포장지 ---
class NewsResponse(BaseModel):
    source: str
    title: str
    link: str
    pubDate: str
    is_translated: bool

# --- 관심종목 포장지 ---
# 관심종목 추가(입력)
class InterestCreate(BaseModel):
    ticker: str     # 종목 코드
    category: str = "stock" # 기본값이 stock

# 관심종목 보여주기(출력)
class InterestResponse(BaseModel):
    id: int
    ticker: str
    category: str
    user_id: int

    class Config:
        from_attributes = True # ORM 모드 켜기

# 차트 그리기
# 과거 데이터 (날짜, 가격)
class HistoryPoint(BaseModel):
    date: str
    price: float

# 과거 데이터 리스트 응답
class HistoryResponse(BaseModel):
    ticker: str
    history: List[HistoryPoint]

# AI 브리핑 응답 포장지
class AiBriefingResponse(BaseModel):
    ticker: str
    briefing: str

