#!/usr/bin/env python3
"""
Stock Analysis Web Dashboard - FIXED VERSION
A cross-platform Flask application for stock analysis with retry logic
"""

import sys
import os
import time

# --- VERSION CHECK ---
if sys.version_info < (3, 7):
    print("❌ Error: Python 3.7+ is required")
    sys.exit(1)

try:
    import yfinance as yf
    import pandas as pd
    import numpy as np
    from sklearn.linear_model import LinearRegression
    import datetime as dt
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    import requests
    import xml.etree.ElementTree as ET
    from nltk.sentiment.vader import SentimentIntensityAnalyzer
    import nltk
    from flask import Flask, request, jsonify
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("\n📦 Installing required packages...")
    os.system("pip install -r requirements.txt")
    print("\n✅ Installation complete! Please run the script again.")
    sys.exit(1)

# --- NLTK SETUP ---
try:
    nltk.data.find('sentiment/vader_lexicon.zip')
except LookupError:
    print("📥 Downloading VADER sentiment lexicon...")
    nltk.download('vader_lexicon', quiet=True)

app = Flask(__name__)

# --- CONFIGURATION ---
COMMON_STOCKS = [
    "IRB.NS", "TCS.NS", "INFY.NS", "WIPRO.NS", "HCLTECH.NS",
    "RELIANCE.NS", "HDFC.NS", "ICICIBANK.NS", "SBIN.NS", "BAJAJFINSV.NS",
    "ADANIPORTS.NS", "MARUTI.NS", "NTPC.NS", "POWERGRID.NS", "COAL.NS"
]

DEFAULT_STOCK = "IRB.NS"
MAX_RETRIES = 3


def fetch_stock_data(symbol, retries=MAX_RETRIES):
    """Fetch stock data with retry logic for reliability"""
    for attempt in range(retries):
        try:
            print(f"📥 Fetching data for {symbol} (attempt {attempt + 1}/{retries})...")
            df = yf.download(symbol, period='1y', interval='1d', progress=False)
            
            if df is None or df.empty:
                if attempt < retries - 1:
                    print(f"⚠️ Empty result, retrying...")
                    time.sleep(1)
                continue
            
            return df.reset_index()
            
        except Exception as e:
            error_msg = str(e)[:60]
            print(f"⚠️ Attempt {attempt + 1} failed: {error_msg}")
            
            if attempt < retries - 1:
                print(f"🔄 Retrying in 2 seconds...")
                time.sleep(2)
    
    print(f"❌ Failed to fetch data after {retries} attempts")
    return None

def get_ticker_from_name(query):
    """Dynamically find ticker from company name using Yahoo API"""
    query = str(query).strip()
    
    # If it's likely already a ticker (no spaces, mostly uppercase)
    if " " not in query and sum(1 for c in query if c.isupper()) > len(query) / 2:
        if not (query.endswith('.NS') or query.endswith('.BO')):
            return query.upper() + ".NS"
        return query.upper()
        
    url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}"
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })
    
    try:
        response = session.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            quotes = data.get('quotes', [])
            
            # Look for NSE or BSE matches
            for quote in quotes:
                symbol = quote.get('symbol', '')
                exchange = quote.get('exchange', '')
                if exchange in ['NSI', 'BSE'] or symbol.endswith('.NS') or symbol.endswith('.BO'):
                    return symbol
                    
            if quotes:
                return quotes[0].get('symbol', '')
                
    except Exception as e:
        print(f"⚠️ Search error for {query}: {e}")
        
    # Fallback to the original dumb behavior if API fails
    fallback = query.replace(" ", "").upper()
    if not (fallback.endswith('.NS') or fallback.endswith('.BO')):
        return fallback + ".NS"
    return fallback


def generate_dashboard(symbol):
    """Generate stock dashboard for given symbol"""
    
    # 1. AUTO-FIX TICKER (Use new search API)
    original_query = symbol
    symbol = get_ticker_from_name(symbol)
    
    print(f"--- 🚀 ANALYZING: {symbol} (from '{original_query}') ---")

    try:
        # --- PART 1: FETCH DATA with RETRIES ---
        df = fetch_stock_data(symbol, retries=MAX_RETRIES)
        if df is None or df.empty:
            print(f"❌ No data available for {symbol}")
            return None

        # Flatten MultiIndex columns if present
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)

        # --- PART 2: NEWS & SENTIMENT ---
        print("📡 Fetching news...")
        encoded_symbol = symbol.replace(".NS", "").replace(".BO", "")
        rss_url = f"https://news.google.com/rss/search?q={encoded_symbol}+stock+india&hl=en-IN&gl=IN&ceid=IN:en"

        vader = SentimentIntensityAnalyzer()
        sentiment_score = 0
        news_count = 0
        latest_headlines = []

        try:
            response = requests.get(rss_url, timeout=5)
            root = ET.fromstring(response.content)
            
            for item in root.findall('.//item')[:10]:
                title_elem = item.find('title')
                pubDate_elem = item.find('pubDate')
                
                if title_elem is not None and pubDate_elem is not None:
                    title = title_elem.text
                    pubDate = pubDate_elem.text
                    
                    score = vader.polarity_scores(title)['compound']
                    sentiment_score += score
                    news_count += 1
                    
                    sentiment_label = "🟢" if score > 0.05 else "🔴" if score < -0.05 else "⚪"
                    latest_headlines.append(f"{sentiment_label} {title} ({pubDate[:16]})")

            avg_sentiment = sentiment_score / news_count if news_count > 0 else 0
        except Exception as e:
            print(f"⚠️ News error: {str(e)[:40]}")
            avg_sentiment = 0

        # --- PART 3: PREDICTION MODEL ---
        print("🤖 Running ML model...")
        
        if len(df) < 10:
            print("⚠️ Not enough data for prediction")
            return None
            
        df['Date_Ordinal'] = df['Date'].map(dt.datetime.toordinal)
        X = df[['Date_Ordinal']]
        y = df['Close']
        model = LinearRegression()
        model.fit(X, y)

        last_date = df['Date'].iloc[-1]
        tomorrow_date = last_date + dt.timedelta(days=1)
        if tomorrow_date.weekday() >= 5:
            tomorrow_date += dt.timedelta(days=(7 - tomorrow_date.weekday()))

        tomorrow_ordinal = np.array([[tomorrow_date.toordinal()]])
        base_price = float(model.predict(tomorrow_ordinal)[0])

        volatility = 0.025
        news_impact = base_price * (avg_sentiment * volatility)
        predicted_close = base_price + news_impact

        recent_volatility = (df['High'] - df['Low']).tail(14).mean()
        predicted_high = predicted_close + (recent_volatility * 0.8)
        predicted_low = predicted_close - (recent_volatility * 0.8)

        # --- PART 4: CREATE CHART ---
        print("🎨 Creating chart...")
        
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                            vertical_spacing=0.05, row_heights=[0.7, 0.3],
                            subplot_titles=(f"{symbol} Price Action", "Volume"))

        fig.add_trace(go.Candlestick(x=df['Date'],
                        open=df['Open'], high=df['High'],
                        low=df['Low'], close=df['Close'],
                        name='OHLC'), row=1, col=1)

        fig.add_trace(go.Scatter(x=df['Date'], y=model.predict(X),
                                 mode='lines', name='Trend Line',
                                 line=dict(color='orange', width=1, dash='dot')), row=1, col=1)

        fig.add_trace(go.Scatter(x=[tomorrow_date], y=[predicted_close],
                                 mode='markers+text', name='Prediction',
                                 marker=dict(color='cyan', size=15, symbol='star'),
                                 text=[f"{predicted_close:.1f}"], textposition="top center"), row=1, col=1)

        fig.add_trace(go.Scatter(x=[tomorrow_date, tomorrow_date], 
                                 y=[predicted_low, predicted_high],
                                 mode='lines', name='Pred Range',
                                 line=dict(color='cyan', width=4)), row=1, col=1)

        colors = ['red' if row['Open'] - row['Close'] >= 0 else 'green' for index, row in df.iterrows()]
        fig.add_trace(go.Bar(x=df['Date'], y=df['Volume'], name='Volume', marker_color=colors), row=2, col=1)

        last_close = df['Close'].iloc[-1]
        change = last_close - df['Close'].iloc[-2]
        pct_change = (change / df['Close'].iloc[-2]) * 100
        color_change = "green" if change >= 0 else "red"

        dashboard_title = (
            f"<b>{symbol}</b>: ₹{last_close:.2f} "
            f"<span style='color:{color_change}'>({change:+.2f} / {pct_change:+.2f}%)</span><br>"
            f"<span style='font-size: 14px; color: gray'>Mood: {avg_sentiment:.3f}</span>"
        )

        fig.update_layout(
            title=dashboard_title,
            yaxis_title='Price (INR)',
            template='plotly_dark',
            height=800,
            showlegend=False,
            hovermode="x unified"
        )

        # --- PART 5: GENERATE HTML ---
        html_content = f"""
<html>
<head><style>
body{{font-family: sans-serif; background-color: #111; color: #ddd; text-align: center;}}
.box{{display: inline-block; background: #222; padding: 20px; margin: 10px; border-radius: 10px; border: 1px solid #444; vertical-align: top; width: 300px;}}
h2{{color: #00ccff;}} .pos{{color: #00ff00;}} .neg{{color: #ff3333;}}
.selector{{padding: 20px; background: #222; border-radius: 10px; margin: 20px; border: 2px solid #00ccff;}}
select, input{{padding: 10px; font-size: 16px; border-radius: 5px; background: #111; color: #0ff; border: 1px solid #0ff; cursor: pointer;}}
input{{width: 200px;}}
button{{padding: 10px 20px; margin-left: 10px; font-size: 16px; border-radius: 5px; background: #00ccff; color: #111; border: none; cursor: pointer; font-weight: bold;}}
button:hover{{background: #00ffff;}}
hr{{border: 1px solid #444; width: 50%;}}
.error-msg{{background: #ff333344; padding: 10px; border-radius: 5px; margin: 10px; color: #ff6666;}}
</style></head>
<body>
    <div class="selector">
        <h1>🤖 AI Stock Report Dashboard</h1>
        <h3 style="color: #00ccff;">📊 Current Stock: <b>{symbol}</b></h3>
        
        <form method="GET" action="/" style="margin-bottom: 20px;">
            <label for="symbol" style="font-size: 18px; color: #00ccff;"><b>Select Stock:</b></label><br><br>
            <select name="symbol" id="symbol">
                <option value="">-- Choose a stock --</option>
                {''.join([f'<option value="{s}">{s}</option>' for s in COMMON_STOCKS])}
            </select>
            <button type="submit">Analyze</button>
        </form>
        
        <hr>
        
        <form method="GET" action="/">
            <label style="font-size: 18px; color: #00ccff;"><b>Search Custom Stock:</b></label><br><br>
            <input type="text" name="symbol" placeholder="e.g., TATAMOTORS, ADANIGREEN" required>
            <button type="submit">Search</button>
        </form>
    </div>

    <h2 style="color: #00ccff; margin-top: 40px;">📊 Analysis Results</h2>
    
    <div class="box">
        <h2>📅 Previous Day</h2>
        <p><b>Date:</b> {last_date.date()}</p>
        <p><b>Close:</b> ₹{last_close:.2f}</p>
        <p><b>High:</b> ₹{df['High'].iloc[-1]:.2f}</p>
        <p><b>Low:</b> ₹{df['Low'].iloc[-1]:.2f}</p>
        <p><b>Vol:</b> {int(df['Volume'].iloc[-1]/1000)}k</p>
    </div>

    <div class="box">
        <h2>🚀 Tomorrow's Prediction</h2>
        <p><b>Target Date:</b> {tomorrow_date.date()}</p>
        <p style="font-size: 20px; font-weight: bold; color: cyan;">Target: ₹{predicted_close:.2f}</p>
        <p><b>Likely High:</b> ₹{predicted_high:.2f}</p>
        <p><b>Likely Low:</b> ₹{predicted_low:.2f}</p>
        <p><i>(News adjusted by {avg_sentiment:.2f})</i></p>
    </div>

    <div class="box" style="width: 600px; text-align: left;">
        <h2>📰 Top Market News</h2>
        <ul style="font-size: 13px; line-height: 1.6;">
            {''.join([f'<li>{h}</li>' for h in latest_headlines]) if latest_headlines else '<li>No news found</li>'}
        </ul>
    </div>
</body>
</html>
"""

        chart_html = fig.to_html(include_plotlyjs='cdn')
        final_report = chart_html.replace("<body>", "<body>" + html_content)
        
        print("✅ Dashboard generated successfully")
        return final_report
    
    except Exception as e:
        print(f"❌ Error generating dashboard: {e}")
        return None


# --- FLASK ROUTES ---
@app.route('/')
def dashboard():
    """Main dashboard route"""
    symbol = request.args.get('symbol', DEFAULT_STOCK).strip()
    
    if not symbol:
        symbol = DEFAULT_STOCK
    
    print(f"\n📨 Request received for: {symbol}")
    result = generate_dashboard(symbol)
    
    if result is None:
        error_html = f"""
        <html>
        <head><style>
        body{{background: #111; color: #ddd; font-family: sans-serif; text-align: center; padding: 50px;}}
        h1{{color: #ff3333;}}
        p{{font-size: 18px;}}
        a{{color: #00ccff; text-decoration: none; font-size: 18px;}}
        a:hover{{text-decoration: underline;}}
        .error-box{{background: #ff333344; padding: 30px; border-radius: 10px; margin: 20px; border: 2px solid #ff6666;}}
        </style></head>
        <body>
        <div class="error-box">
            <h1>❌ Data Not Available</h1>
            <p>Stock '{symbol}' not found or Yahoo Finance API is temporarily unavailable.</p>
            <p>Please try:</p>
            <ul>
                <li>Check the stock symbol is correct</li>
                <li>Try another stock from the list</li>
                <li>Wait a minute and refresh</li>
            </ul>
        </div>
        <p><a href="/">← Go Back to Dashboard</a></p>
        </body>
        </html>
        """
        return error_html, 200
    
    return result


@app.route('/api/stocks')
def get_stocks():
    """API endpoint to get available stocks"""
    return jsonify({"stocks": COMMON_STOCKS})


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok", "version": "1.1"}), 200


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🤖 AI STOCK ANALYSIS DASHBOARD v1.1")
    print("="*60)
    
    import socket
    
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
    except:
        local_ip = "127.0.0.1"
    
    port = int(os.environ.get('PORT', 5000))
    
    print(f"\n✅ Server starting...")
    print(f"📍 Local:     http://127.0.0.1:{port}")
    print(f"📍 Network:   http://{local_ip}:{port}")
    print(f"\n💡 Tip: If data not found, wait 30 sec and refresh")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=port, debug=False)
