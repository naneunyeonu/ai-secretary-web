# app/crud.py
from sqlalchemy.orm import Session
from app import models, schemas, utils

# 1. 이메일로 유저 찾기 (중복 가입 방지용)
def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

# 2. 유저 생성하기 (회원가입)
def create_user(db: Session, user: schemas.UserCreate):
    # (1) 비밀번호 암호화 ("1234" -> "xkdl@#...")
    fake_hashed_password = utils.get_password_hash(user.password)
    
    # (2) DB 모델 객체 만들기
    db_user = models.User(
        email=user.email,
        hashed_password=fake_hashed_password, # 암호화된 비번 저장
        nickname=user.nickname
    )
    
    # (3) DB에 저장
    db.add(db_user)
    db.commit()      # 확정!
    db.refresh(db_user) # 저장된 정보를 다시 받아옴 (ID 등을 알기 위해)
    
    return db_user