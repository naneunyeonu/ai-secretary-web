# app/ai_analyst.py
import os
import google.generativeai as genai
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# Gemini 설정
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

def analyze_market_data(ticker, price_info, news_list):
    """
    종목(ticker), 가격 정보(price_info), 뉴스(news_list)를 받아
    Gemini에게 등락 원인 분석을 요청합니다.
    """
    try:
        # 1. 사용할 모델 선택 (Gemini Pro 또는 1.5 Flash)
        model = genai.GenerativeModel('gemini-flash-latest')

        # 2. 뉴스 리스트를 텍스트로 변환
        news_text = ""
        for idx, news in enumerate(news_list, 1):
            news_text += f"{idx}. {news['title']} ({news['source']})\n"

        # 3. 프롬프트(명령어) 작성 - 여기가 핵심!
        prompt = f"""
        당신은 월가에서 20년 경력을 가진 유능한 '금융 애널리스트'입니다.
        아래 데이터를 바탕으로 '{ticker}' 종목의 현재 상황과 등락 원인을 분석해서 브리핑해주세요.

        [시장 데이터]
        - 현재가: {price_info.get('price')}
        - 등락률: {price_info.get('change_percent')}%

        [최신 뉴스 헤드라인]
        {news_text}

        [작성 원칙]
        1. **등락의 핵심 원인**을 뉴스에 기반하여 논리적으로 설명하세요.
        2. 상승/하락 여부에 따라 긍정적/부정적 요인을 명확히 짚어주세요.
        3. 단순한 뉴스 나열이 아니라, 투자자가 이해하기 쉬운 **'인사이트'**를 제공하세요.
        4. 말투는 "~했습니다.", "~보입니다."와 같은 **전문적이고 정중한 '해요체'**를 사용하세요.
        5. 분량은 반드시 **공백 포함 한글 350자 이상, 500자 이하**로 작성하세요.
        6. 글의 시작을 "현재 {ticker}의 주가는..." 으로 시작하지 마세요. 바로 핵심 분석으로 들어가세요.
        """

        # 4. AI에게 질문 던지기
        response = model.generate_content(prompt)
        return response.text

    except Exception as e:
        print(f"🚨 AI Analysis Error: {e}")
        return "죄송합니다. 현재 AI 분석 서버 연결이 지연되고 있습니다. 잠시 후 다시 시도해주세요."