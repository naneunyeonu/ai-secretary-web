# app/finance.py
import yfinance as yf
import requests
import os
from dotenv import load_dotenv
import re
import xml.etree.ElementTree as ET  # 구글 뉴스 RSS 해석용

load_dotenv()

NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

# 1. 가격 정보 가져오기 (기존 로직 유지 + 안전장치)
def get_current_price(ticker_symbol: str):
    try:
        ticker_symbol = ticker_symbol.strip().upper()
        # 환율 티커 처리 (KRW=X 등)
        is_forex = "=X" in ticker_symbol or "-" in ticker_symbol
        
        ticker = yf.Ticker(ticker_symbol)
        
        # fast_info 사용 시도
        try:
            price = ticker.fast_info.last_price
            previous_close = ticker.fast_info.previous_close
            currency = ticker.fast_info.currency
        except:
            # 실패시 history 사용
            hist = ticker.history(period="5d")
            if hist.empty: return None
            price = hist['Close'].iloc[-1]
            previous_close = hist['Close'].iloc[-2] if len(hist) > 1 else price
            # 통화 정보가 없으면 대충 추정
            currency = "KRW" if ".KS" in ticker_symbol or ticker_symbol == "KRW=X" else "USD"

        # 변동률 계산
        change_rate = 0.0
        if previous_close and previous_close > 0:
            change_rate = ((price - previous_close) / previous_close) * 100

        return {
            "code": ticker_symbol,
            "price": round(price, 2),
            "change_percent": round(change_rate, 2),
            "currency": currency
        }
    except Exception as e:
        print(f"🚨 Price Error ({ticker_symbol}): {e}")
        return None

# 2. 통합 뉴스 가져오기 (네이버 5 + 구글 RSS 5)
# RSS -> XML을 가져와서 읽기
def get_integrated_news(ticker_symbol: str):
    news_list = []
    
    # (A) 네이버 뉴스 (국내 5개) - 기존 유지
    try:
        search_query = ticker_symbol
        url = "https://openapi.naver.com/v1/search/news.json"
        headers = {
            "X-Naver-Client-Id": NAVER_CLIENT_ID,
            "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
        }
        params = {"query": search_query, "display": 5, "sort": "sim"}
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            items = response.json().get("items", [])
            for item in items:
                clean_title = re.sub('<[^<]+?>', '', item['title'])
                clean_title = clean_title.replace("&quot;", '"').replace("&amp;", "&")
                
                news_list.append({
                    "title": clean_title,
                    "link": item['originallink'] if item['originallink'] else item['link'],
                    "source": "Domestic (Naver)",
                    "pubDate": item['pubDate']
                })
    except Exception as e:
        print(f"⚠️ Naver News Error: {e}")

    # (B) 구글 뉴스 RSS (해외 5개) - [신규] 야후 대체 🚀
    try:
        # 검색어 설정: 티커 + "stock" (예: VOO stock)
        rss_query = f"{ticker_symbol} stock"
        # 구글 뉴스 RSS 주소 (미국/영어 설정)
        rss_url = f"https://news.google.com/rss/search?q={rss_query}&hl=en-US&gl=US&ceid=US:en"
        
        rss_res = requests.get(rss_url, timeout=5)
        
        if rss_res.status_code == 200:
            # XML 데이터 파싱 (분해)
            root = ET.fromstring(rss_res.text)
            
            # <item> 태그 찾기 (뉴스 기사들)
            count = 0
            for item in root.findall('./channel/item'):
                if count >= 5: break # 5개 제한
                
                title = item.find('title').text
                link = item.find('link').text
                pub_date = item.find('pubDate').text
                
                news_list.append({
                    "title": title,
                    "link": link,
                    "source": "Global (Google)", # 출처 변경
                    "pubDate": pub_date
                })
                count += 1
    except Exception as e:
        print(f"⚠️ Google RSS Error: {e}")

    return news_list

# 3. 차트 데이터 (기존 유지)
def get_price_history(ticker_symbol: str):
    try:
        ticker = yf.Ticker(ticker_symbol.strip().upper())
        # [수정] 1달 -> 3달치 데이터로 변경 요청 반영
        hist = ticker.history(period="3mo") 
        
        if hist.empty: return None

        history_list = []
        for date, row in hist.iterrows():
            date_str = date.strftime("%Y-%m-%d")
            history_list.append({
                "date": date_str,
                "price": row['Close']
            })
            
        return {"ticker": ticker_symbol, "history": history_list}
    except Exception:
        return None

# ======================================================================
# 주요 지수(Indices) 데이터 가져오기
# ======================================================================
def get_major_indices():
    # 야후 파이낸스 티커 기준
    indices = {
        "KOSPI": "^KS11",
        "NASDAQ": "^IXIC",
        "S&P 500": "^GSPC",
        "Nikkei 225": "^N225"
    }
    
    results = []
    for name, ticker_symbol in indices.items():
        data = get_current_price(ticker_symbol) # 기존 함수 재사용
        if data:
            data['name'] = name # 사람이 읽기 쉬운 이름 추가
            results.append(data)
            
    return results

# 지수 차트 데이터 (3개월) - 범용 함수
def get_price_history_custom(ticker_symbol: str, period: str = "3mo"):
    try:
        ticker = yf.Ticker(ticker_symbol.strip().upper())
        hist = ticker.history(period=period)
        
        if hist.empty: return None

        history_list = []
        for date, row in hist.iterrows():
            date_str = date.strftime("%Y-%m-%d")
            history_list.append({
                "date": date_str,
                "price": row['Close']
            })
            
        return {"ticker": ticker_symbol, "history": history_list}
    except Exception:
        return None
    
# app/finance.py에 추가

def get_exchange_rate():
    """실시간 USD/KRW 환율을 가져옵니다."""
    try:
        ticker = yf.Ticker("KRW=X")
        return ticker.fast_info.last_price
    except Exception as e:
        print(f"⚠️ 환율 조회 실패: {e}")
        return 1400.0 # 실패 시 임시 기본값