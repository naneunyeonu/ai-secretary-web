# app/main.py
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import models, schemas, crud
from app.database import engine, get_db

# 로그인 API 만들기
from fastapi.security import OAuth2PasswordRequestForm
from app import utils

# 의존성 함수 get_current_user
from fastapi.security import OAuth2PasswordBearer  # <--- 토큰 추출기
from jose import jwt, JWTError                     # <--- 토큰 해독기
from app import models, schemas, crud, utils, finance, news_collector
from typing import List     # 리스트 형태를 쓰기 위해 필요

# 서버와 HTML 연결하기
from fastapi import Request
from fastapi.templating import Jinja2Templates  # 템플릿 엔진 추가
from fastapi.responses import HTMLResponse      # HTML 응답 추가

# AI 모듈 가져오기
from app import ai_analyst


# 1. DB 테이블 자동 생성 (혹시 안 만들어진 게 있다면)
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# HTML 템플릿 폴더 지정
templates = Jinja2Templates(directory="app/templates")

# 2. 회원가입 API (POST /signup)
@app.post("/signup", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # (1) 이메일 중복 검사
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다.")
    
    # (2) 유저 생성 (CRUD에게 시킴)
    return crud.create_user(db=db, user=user)

# 4. 로그인 API (POST /login)
@app.post("/login", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # (1) 이메일로 유저 찾기
    user = crud.get_user_by_email(db, email=form_data.username) # OAuth2 폼에서는 email을 username이라고 부름
    
    # (2) 유저가 없거나 비밀번호가 틀리면 에러
    if not user or not utils.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 잘못되었습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # (3) 로그인 성공! 토큰 발급
    access_token = utils.create_access_token(data={"sub": user.email})
    
    return {"access_token": access_token,
            "token_type": "bearer",
            "nickname": user.nickname if user.nickname else "사용자"}

# ===== 의존성 함수 =====
# 1. 토큰을 어디서 가져올지 설정 (Url="login"은 Swagger UI에서 자물쇠 버튼을 누르면 login API를 호출하라는 뜻)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# 2. 현재 로그인한 사용자 가져오기 (경비원 함수)
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    # 자격 증명 실패 시 내보낼 에러 메시지 미리 준비
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="자격 증명을 검증할 수 없습니다 (유효하지 않은 토큰).",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # (1) 토큰 해독 (utils에 있는 비밀키 사용)
        payload = jwt.decode(token, utils.SECRET_KEY, algorithms=[utils.ALGORITHM])
        email: str = payload.get("sub") # 토큰 안에 'sub'라는 이름으로 이메일이 들어있음
        
        if email is None:
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception # 토큰이 위조되었거나 만료됨
        
    # (2) 해독된 이메일로 진짜 유저가 DB에 있는지 확인
    user = crud.get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception
        
    return user

# 3. 내 정보 보기 API (보호된 라우트 테스트용)
# 이 함수는 'user'라는 변수에 'get_current_user'가 리턴한 값(현재 로그인한 유저 객체)을 자동으로 주입받습니다.
@app.get("/users/me", response_model=schemas.UserResponse)
def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user

# 3. 테스트용 (서버 상태 확인)
@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    # base.html 을 상속받은 index.html 예정
    return templates.TemplateResponse("base.html", {"request": request})

# 로그인 페이지 보이기 (GET)
@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# 회원가입 페이지 보이기 (GET)
@app.get("/signup", response_class=HTMLResponse)
def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

# 대시보드 보여주기
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


# ---------------------------------------------------------
# 4. 자산 정보 (주가/환율) 실시간 조회 API
# ---------------------------------------------------------
@app.get("/assets/price/{ticker}", response_model=schemas.PriceResponse)
def read_asset_price(ticker: str, user: models.User = Depends(get_current_user)):
    """
    특정 종목(ticker)의 현재가를 가져옵니다. 
    (로그인한 사람만 볼 수 있게 경비원(Depends)을 세워뒀습니다)
    """
    # 1. finance.py 사용
    data = finance.get_current_price(ticker)

    if not data:
        raise HTTPException(status_code=404, detail="데이터를 찾을 수 없습니다.")

    return data

# ---------------------------------------------------------
# 5. 뉴스 실시간 조회 API (네이버 5 + yfinance 5)
# ---------------------------------------------------------
@app.get("/assets/news/{ticker}")
def read_asset_news(ticker: str, user: models.User = Depends(get_current_user)):
    """
    특정 종목의 통합 뉴스(국내+해외)를 가져옵니다.
    """
    # finance.py에 만든 통합 수집 함수 사용 (ticker만 넘겨주면 됨)
    news_list = finance.get_integrated_news(ticker)
    
    if not news_list:
        return []
        
    return news_list


# ---------------------------------------------------------
# 6. 관심 종목 관리 API(찜하기)
# ---------------------------------------------------------

# 6-1. 관심종목 추가 (POST)
@app.post("/interests", response_model=schemas.InterestCreate)
def create_interest(interest: schemas.InterestCreate,
                    db: Session = Depends(get_db),
                    user: models.User = Depends(get_current_user)):
    """
    관심 종목을 디비에 저장. (이미 있는건 중복 저장 안함)
    """
    # 1. 중복확인
    existing_interest = db.query(models.UserInterest).filter(
        models.UserInterest.user_id == user.id,
        models.UserInterest.ticker == interest.ticker
    ).first()

    if existing_interest:
        raise HTTPException(status_code=400, detail="이미 관심 종목에 등록되어 있습니다.")

    # 2. 중복X 새로 저장
    new_interest = models.UserInterest(
        ticker = interest.ticker,
        category=interest.category,
        user_id = user.id
    )
    db.add(new_interest)
    db.commit()
    db.refresh(new_interest)
    return new_interest

# 6-2. 내 관심 목록 조회 (GET)
@app.get("/interests", response_model=List[schemas.InterestResponse])
def read_interests(db: Session = Depends(get_db), 
                   user: models.User = Depends(get_current_user)):
    """
    로그인한 사용자의 모든 관심 종목을 가져옵니다.
    """
    return user.interests

# 6-3. 관심 종목 삭제 (DELETE)
@app.delete("/interests/{ticker}")
def delete_interest(ticker: str, 
                    db: Session = Depends(get_db), 
                    user: models.User = Depends(get_current_user)):
    """
    특정 종목(ticker)을 관심 목록에서 삭제합니다.
    """
    # 1. 삭제할 대상을 찾음 (내 아이디 + 티커)
    target = db.query(models.UserInterest).filter(
        models.UserInterest.user_id == user.id,
        models.UserInterest.ticker == ticker
    ).first()
    
    if not target:
        raise HTTPException(status_code=404, detail="해당 종목이 관심 목록에 없습니다.")
    
    # 2. 삭제 실행
    db.delete(target)
    db.commit()
    return {"msg": f"{ticker} 삭제 완료"}

# 7. 주가 차트 데이터 조회 API 
@app.get("/assets/history/{ticker}", response_model=schemas.HistoryResponse)
def read_asset_history(ticker: str,
                       user: models.User = Depends(get_current_user)):
    """
    특정 종목의 1달치 추가 차트용 흐름 데이터를 가져옴
    """
    data = finance.get_price_history(ticker)

    if not data:
        raise HTTPException(status_code=404, detail="과거 데이터를 불러올 수 없습니다.")
    
    return data


# 8. AI 브리핑 조회 API
@app.get("/assets/briefing/{ticker}", response_model=schemas.AiBriefingResponse)
def read_asset_briefing(ticker: str, user: models.User = Depends(get_current_user)):
    """
    종목의 가격과 뉴스를 종합하여 AI가 등락 원인을 분석해줍니다.
    """
    # 1. 가격 정보 가져오기
    price_info = finance.get_current_price(ticker)
    if not price_info:
        raise HTTPException(status_code=404, detail="가격 정보를 찾을 수 없습니다.")

    # 2. 통합 뉴스 가져오기
    news_list = finance.get_integrated_news(ticker)
    
    # 3. AI에게 분석 요청 (시간이 2~3초 걸림)
    briefing_text = ai_analyst.analyze_market_data(ticker, price_info, news_list)
    
    return {
        "ticker": ticker,
        "briefing": briefing_text
    }


# ======================================================================
# 홈 화면 항목
# ======================================================================
# app/main.py (맨 아래에 추가)

# [홈] 1. 주요 지수 목록 조회
@app.get("/home/indices")
def read_home_indices():
    return finance.get_major_indices()

# [홈] 3. 차트 데이터 조회 (지수용 - 3개월)
@app.get("/home/chart/{ticker}")
def read_home_chart(ticker: str):
    # 특수문자 처리 (KOSPI 등은 URL에서 문제가 될 수 있으므로 매핑)
    ticker_map = {
        "KOSPI": "^KS11",
        "NASDAQ": "^IXIC",
        "S_P500": "^GSPC", # URL엔 &를 못 써서 _로 받을 예정
        "NIKKEI": "^N225"
    }
    real_ticker = ticker_map.get(ticker, ticker)
    return finance.get_price_history_custom(real_ticker, period="3mo")