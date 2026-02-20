# app/news_collector.py
import requests
import os
import yfinance as yf
from dotenv import load_dotenv
from deep_translator import GoogleTranslator
from datetime import datetime

load_dotenv()
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

# --- 1. 번역 도구 ---
def translate_to_korean(text):
    """영어를 한국어로 번역합니다."""
    try:
        if not text:
            return ""
        translator = GoogleTranslator(source='auto', target='ko')
        return translator.translate(text)
    except Exception as e:
        print(f"Translation Error: {e}")
        return text

# --- 2. 네이버 뉴스 (한국) ---
def get_naver_news(keyword: str, limit: int):
    if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
        print("🚨 오류: .env 파일에 네이버 API 키가 없습니다!")
        return []

    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }
    params = {"query": keyword, "display": limit, "sort": "sim"}

    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            items = response.json().get("items", [])
            news_list = []
            for item in items:
                news_list.append({
                    "source": "Naver",
                    "title": remove_html_tags(item['title']),
                    "link": item['link'],
                    "pubDate": item['pubDate'],
                    "is_translated": False
                })
            return news_list
        else:
            print(f"Naver API Error Code: {response.status_code}")
            return []
    except Exception as e:
        print(f"Naver Connection Error: {e}")
        return []

# --- 3. 야후 뉴스 (미국/글로벌) ---
def get_yahoo_news(ticker_code: str, limit: int):
    try:
        ticker = yf.Ticker(ticker_code)
        news_items = ticker.news
        
        # 뉴스 데이터가 없으면 빈 리스트 반환
        if not news_items:
            return []

        selected_news = news_items[:limit]
        result_list = []
        
        for item in selected_news:
            # [수정된 부분] 데이터가 'content'라는 키 안에 숨어있는지 확인
            data = item.get('content', item) 
            
            # 제목 추출
            original_title = data.get('title')
            if not original_title:
                continue # 제목 없으면 패스

            # 링크 추출 (clickThroughUrl 안에 url이 있는 구조로 변경됨)
            link = ""
            if 'clickThroughUrl' in data and data['clickThroughUrl']:
                 link = data['clickThroughUrl'].get('url', '')
            else:
                 link = data.get('link', '') # 예전 방식 대비

            # 날짜 추출
            pub_date_str = str(data.get('pubDate', '')) # 이미 문자열로 들어옴
            
            # 번역 실행
            translated_title = translate_to_korean(original_title)
            
            result_list.append({
                "source": "Yahoo(US)",
                "title": f"[번역] {translated_title}",
                "original_title": original_title,
                "link": link,
                "pubDate": pub_date_str,
                "is_translated": True
            })
        return result_list
    except Exception as e:
        print(f"Yahoo News Error: {e}")
        return []

# --- 4. 통합 수집기 (메인 함수) ---
def get_integrated_news(ticker_code: str, company_name: str = None):
    news_results = []
    
    # 한국 주식인지 확인
    is_korean_stock = ticker_code.endswith(".KS") or ticker_code.endswith(".KQ")
    
    search_keyword = company_name if company_name else ticker_code
    
    if is_korean_stock:
        # 한국 주식: 네이버 5개
        print(f"🇰🇷 한국 주식 뉴스 수집: 키워드 '{search_keyword}'")
        news_results.extend(get_naver_news(search_keyword, limit=5))
    else:
        # 미국 주식: 네이버 3개 + 야후 5개 -> 합이 8개
        print(f"🇺🇸 미국 주식 뉴스 수집: 키워드 '{search_keyword}' & Ticker '{ticker_code}'")
        news_results.extend(get_naver_news(search_keyword, limit=3))
        news_results.extend(get_yahoo_news(ticker_code, limit=5))

    return news_results

def remove_html_tags(text):
    return text.replace("<b>", "").replace("</b>", "").replace("&quot;", "\"")