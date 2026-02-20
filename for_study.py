import yfinance as yf

print("=====================함수 공부=====================")

ticker_code1 = "VOO"
ticker_code2 = "GOOG"

ticker1 = yf.Ticker(ticker_code1)
print(ticker1)