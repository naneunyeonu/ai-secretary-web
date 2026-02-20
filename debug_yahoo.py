# debug_yahoo.py
import yfinance as yf
import json

print("--- 야후 뉴스 데이터 정밀 검사 시작 ---")
try:
    ticker = yf.Ticker("AAPL")
    news = ticker.news
    
    print(f"1. 가져온 뉴스 개수: {len(news)}개")
    
    if news:
        print("\n2. 첫 번째 뉴스의 생김새 (Raw Data):")
        # 데이터 딕셔너리를 예쁘게 출력해서 키값(title, link 등)을 확인합니다.
        print(json.dumps(news[0], indent=2, ensure_ascii=False))
    else:
        print("\n⚠️ 경고: 뉴스 리스트가 완전히 비어있습니다.")
        print("해결책: yfinance 버전을 업데이트하거나, 잠시 후 다시 시도해보세요.")

except Exception as e:
    print(f"\n❌ 에러 발생: {e}")