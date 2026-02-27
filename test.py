import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt
import datetime as dt
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk

# --- SETUP ---
# Download the lexicon (dictionary) for sentiment analysis if not already present
try:
    nltk.data.find('sentiment/vader_lexicon.zip')
except LookupError:
    nltk.download('vader_lexicon')

symbol = 'TMPV.ns'  # Change this to any stock you want
print(f"--- Starting Analysis for {symbol} ---")

# --- PART 1: GET STOCK DATA (HISTORY) ---
# We fetch 2 years of data to show "all previous details"
data = yf.download(symbol, period='2y', interval='1d')
data = data.reset_index()

# Prepare data for Linear Regression
data['Date_Ordinal'] = data['Date'].map(dt.datetime.toordinal)
X = data[['Date_Ordinal']]
y = data['Close']

# Train the "Math" Model
model = LinearRegression()
model.fit(X, y)

# --- PART 2: GET NEWS & ANALYZE SENTIMENT ---
print("Fetching latest news...")
ticker = yf.Ticker(symbol)
news_list = ticker.news  # Get latest news list
vader = SentimentIntensityAnalyzer()

sentiment_score = 0
count = 0

# Analyze the headlines
if news_list:
    print(f"\nAnalyzing {len(news_list)} recent headlines:")
    for article in news_list:
        title = article.get('title', '')
        # Get a score: -1 (Negative) to +1 (Positive)
        score = vader.polarity_scores(title)['compound']
        sentiment_score += score
        count += 1
        print(f"  - [{score:+.2f}] {title[:60]}...")
    
    # Average the score
    avg_sentiment = sentiment_score / count
else:
    print("No news found. Assuming Neutral sentiment.")
    avg_sentiment = 0

print(f"\n>>> AVERAGE MARKET MOOD: {avg_sentiment:.4f} (-1=Bearish, +1=Bullish)")

# --- PART 3: PREDICT TOMORROW ---
# Get tomorrow's date
last_date = data['Date'].iloc[-1]
tomorrow_date = last_date + dt.timedelta(days=1)
tomorrow_ordinal = np.array([[tomorrow_date.toordinal()]])

# 1. Base Prediction (Math only)
# ERROR FIX: We wrap the result in float() to ensure it's a number, not an array
base_prediction = float(model.predict(tomorrow_ordinal)[0])

# 2. News Adjustment
# Logic: If news is great (+1), boost price by 2%. If bad (-1), drop by 2%.
volatility_factor = 0.02  
news_adjustment = base_prediction * (avg_sentiment * volatility_factor)
final_prediction = base_prediction + news_adjustment

print(f"\n--- PREDICTION FOR TOMORROW ({tomorrow_date.date()}) ---")
print(f"Technical (Trend) Prediction : ${base_prediction:.2f}")
print(f"News Sentiment Adjustment    : ${news_adjustment:+.2f}")
print(f"FINAL PREDICTED PRICE        : ${final_prediction:.2f}")

# --- PART 4: VISUALIZATION ---
plt.figure(figsize=(12, 6))

# Plot Actual History
plt.plot(data['Date'], data['Close'], label='Historical Close Price', color='blue', alpha=0.6)

# Plot The Trend Line
plt.plot(data['Date'], model.predict(X), label='Linear Trend', color='orange', linestyle='--')

# Plot Tomorrow's Prediction
plt.scatter([tomorrow_date], [final_prediction], color='red', s=100, zorder=5, label='Tomorrow Prediction (News Adjusted)')

plt.title(f"{symbol} Price Prediction (Sentiment Adjusted)")
plt.xlabel("Date")
plt.ylabel("Price (USD)")
plt.legend()
plt.grid(True, alpha=0.3)

# Save the plot
filename = "smart_prediction.png"
plt.savefig(filename)
print(f"\nGraph saved to: {filename}")
