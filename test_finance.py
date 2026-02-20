# test_finance.py
from app.news_collector import get_integrated_news

print("\n>>>>>>>>>> 1. 미국 주식 (애플 AAPL) 테스트 <<<<<<<<<<")
# AAPL 코드와 "애플"이라는 검색어를 같이 넘깁니다.
aapl_news = get_integrated_news("AAPL", "애플")

if not aapl_news:
    print("❌ 결과 없음: API 키 설정이나 인터넷 연결을 확인하세요.")

for news in aapl_news:
    print(f"[{news['source']}] {news['title']}")
    # 링크가 너무 길면 보기 싫으니 잘라서 출력
    print(f"   -> 링크: {news['link'][:60]}...") 


print("\n\n>>>>>>>>>> 2. 한국 주식 (현대차 005380.KS) 테스트 <<<<<<<<<<")
# 코드는 005380.KS 지만, 검색은 "현대차"로 합니다.
hyundai_news = get_integrated_news("005380.KS", "현대차")

if not hyundai_news:
    print("❌ 결과 없음: 네이버 API 키를 확인하세요.")

for news in hyundai_news:
    print(f"[{news['source']}] {news['title']}")
    print(f"   -> 링크: {news['link'][:60]}...") 