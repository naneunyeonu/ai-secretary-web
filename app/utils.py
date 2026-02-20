# app/utils.py
import bcrypt
from datetime import datetime, timedelta
from jose import jwt

# 1. 설정값 (환경변수에서 가져오는 게 좋지만, 일단 여기에 둡니다)
SECRET_KEY = "super-secret-key"  # 실제 배포시엔 .env로 옮겨야 함
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# 2. 비밀번호 암호화 및 검증 (passlib 제거 -> bcrypt 직접 사용)
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    사용자가 입력한 비밀번호(plain)와 DB에 저장된 암호문(hashed)이 일치하는지 확인
    """
    # bcrypt는 bytes 타입을 원하므로 문자열을 bytes로 변환해야 함 (.encode)
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password: str) -> str:
    """
    비밀번호를 암호화해서 문자열로 반환
    """
    # 1. 비밀번호를 bytes로 변환
    pwd_bytes = password.encode('utf-8')
    # 2. 소금(salt)을 쳐서 암호화
    salt = bcrypt.gensalt()
    hashed_bytes = bcrypt.hashpw(pwd_bytes, salt)
    # 3. DB에 저장하기 편하게 다시 문자열로 변환 (.decode)
    return hashed_bytes.decode('utf-8')

# 3. 토큰 생성 (기존과 동일)
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt