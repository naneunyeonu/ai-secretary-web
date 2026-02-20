# app/database.py
# .env 를 읽어서 DB에 접속하는 역할
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# 1. .env 파일 로드
load_dotenv()

# 2. DB 주소 가져오기
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# 3. 엔진 생성 (DB와의 연결 통로)
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# 4. 세션 생성기 (실제 작업할 때 쓰는 도구)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 5. 모델의 기본 클래스 (나중에 테이블 모델 만들 때 씀)
# model.py 의 User, Asset class에서 이 Base를 상속받아야 인식 가능
Base = declarative_base()

# 6. DB 세션 가져오기 (FastAPI에서 쓸 함수)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()