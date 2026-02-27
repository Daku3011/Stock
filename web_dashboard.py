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
import time

# --- SETUP ---
try:
    nltk.data.find('sentiment/vader_lexicon.zip')
except LookupError:
    nltk.download('vader_lexicon')

app = Flask(__name__)

# --- COMMON INDIAN STOCKS ---
COMMON_STOCKS = [
    "IRB.NS", "TCS.NS", "INFY.NS", "WIPRO.NS", "HCL.NS",
    "RELIANCE.NS", "HDFC.NS", "ICICIBANK.NS", "SBIN.NS", "BAJAJFINSV.NS",
    "ADANIPORTS.NS", "MARUTI.NS", "NTPC.NS", "POWERGRID.NS", "COAL.NS",
    "TATAMOTORS.NS", "ITC.NS", "SUNPHARMA.NS"
]

# --- DEFAULT STOCK ---
DEFAULT_STOCK = "IRB.NS"

def calculate_technical_indicators(df):
    """Add SMA and RSI to the dataframe"""
    # 1. SMA 20 (Short term trend)
    df['SMA20'] = df['Close'].rolling(window=20).mean()

    # 2. RSI (Relative Strength Index)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    
    # Avoid division by zero
    loss[loss == 0] = 0.0001
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # Fill NaN values (resulting from rolling windows)
    df.fillna(method='bfill', inplace=True)
    return df

def generate_dashboard(symbol):
    """Generate stock dashboard for given symbol"""
    
    # 1. AUTO-FIX TICKER (Add .NS for India)
    if not (symbol.endswith('.NS') or symbol.endswith('.BO')):
        symbol = symbol + ".NS"
    
    print(f"--- 🚀 STARTING WEB ANALYSIS FOR: {symbol} ---")

    # --- PART 1: FETCH DATA (WITH ANTI-BLOCKING FIX) ---
    df = pd.DataFrame()
    
    # Create a custom session to trick Yahoo
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    })

    # Retry loop in case of timeout
    for attempt in range(3):
        try:
            print(f"📡 Downloading data for {symbol} (Attempt {attempt+1})...")
            # Pass the session to yfinance
            df = yf.download(symbol, period='1y', interval='1d', progress=False, session=session, timeout=10)
            
            if not df.empty:
                break # Success!
            
        except Exception as e:
            print(f"⚠️ Attempt {attempt+1} failed: {e}")
            time.sleep(2) # Wait 2 seconds before retrying

    if df.empty:
        print(f"❌ Error: No data found for {symbol} after 3 attempts.")
        return None
        
    df = df.reset_index()

    # Flatten MultiIndex columns (Fix for new yfinance versions)
    if isinstance(df.columns, pd.MultiIndex):
        try:
            df.columns = df.columns.droplevel(1)
        except:
            pass # Keep columns if droplevel fails
        
    # ** Calculate Indicators **
    df = calculate_technical_indicators(df)

    # --- PART 2: GOOGLE NEWS HACK ---
    print("📡 Fetching Google News (Live)...")
    encoded_symbol = symbol.replace(".NS", "").replace(".BO", "")
    rss_url = f"https://news.google.com/rss/search?q={encoded_symbol}+stock+india&hl=en-IN&gl=IN&ceid=IN:en"

    # Use the same session for News request
    try:
        response = session.get(rss_url, timeout=5)
        vader = SentimentIntensityAnalyzer()
        sentiment_score = 0
        news_count = 0
        latest_headlines = []

        root = ET.fromstring(response.content)
        # Get top 8 news items
        for item in root.findall('.//item')[:8]:
            title = item.find('title').text
            pubDate = item.find('pubDate').text
            
            # Score sentiment
            score = vader.polarity_scores(title)['compound']
            sentiment_score += score
            news_count += 1
            
            # Save for display
            sentiment_label = "🟢" if score > 0.05 else "🔴" if score < -0.05 else "⚪"
            latest_headlines.append(f"{sentiment_label} {title} ({pubDate[:16]})")

        avg_sentiment = sentiment_score / news_count if news_count > 0 else 0

    except Exception as e:
        print(f"⚠️ News Error: {e}")
        avg_sentiment = 0
        latest_headlines = []

    print(f"   >>> Market Mood Score: {avg_sentiment:.4f}")

    # --- PART 3: ADVANCED PREDICTION ---
    # Prepare Math Model
    df['Date_Ordinal'] = df['Date'].map(dt.datetime.toordinal)
    X = df[['Date_Ordinal']]
    y = df['Close']
    model = LinearRegression()
    model.fit(X, y)

    # Predict Tomorrow
    last_date = df['Date'].iloc[-1]
    tomorrow_date = last_date + dt.timedelta(days=1)
    if tomorrow_date.weekday() >= 5: # If Sat/Sun, jump to Monday
        tomorrow_date += dt.timedelta(days=(7 - tomorrow_date.weekday()))

    tomorrow_ordinal = np.array([[tomorrow_date.toordinal()]])
    base_price = float(model.predict(tomorrow_ordinal)[0])

    # Apply Sentiment Adjustment
    volatility = 0.025 # 2.5% sway based on news
    news_impact = base_price * (avg_sentiment * volatility)
    
    # ** RSI Adjustment **
    # If RSI > 70 (Overbought), dampen the target
    # If RSI < 30 (Oversold), boost the target
    current_rsi = df['RSI'].iloc[-1]
    rsi_factor = 1.0
    
    if current_rsi > 70:
        rsi_factor = 0.99  # 1% Pullback expected
    elif current_rsi < 30:
        rsi_factor = 1.01  # 1% Bounce expected

    predicted_close = (base_price + news_impact) * rsi_factor

    # ESTIMATE RANGE (High/Low) based on recent volatility
    recent_volatility = (df['High'] - df['Low']).tail(14).mean()
    predicted_high = predicted_close + (recent_volatility * 0.8)
    predicted_low = predicted_close - (recent_volatility * 0.8)

    # --- PART 4: GENERATE WEB CHART (PLOTLY) ---
    print("🎨 Generating Web Dashboard...")

    # Create Subplots (Chart on top, Volume Middle, RSI Bottom)
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.02, row_heights=[0.5, 0.25, 0.25],
                        subplot_titles=(f"{symbol} Price Action", "Volume", "RSI (Momentum)"))

    # A. Candlestick Chart
    fig.add_trace(go.Candlestick(x=df['Date'],
                    open=df['Open'], high=df['High'],
                    low=df['Low'], close=df['Close'],
                    name='OHLC'), row=1, col=1)

    # B. Trend Line
    fig.add_trace(go.Scatter(x=df['Date'], y=model.predict(X),
                             mode='lines', name='Trend Line',
                             line=dict(color='orange', width=1, dash='dot')), row=1, col=1)
    
    # ** SMA 20 Overlay **
    fig.add_trace(go.Scatter(x=df['Date'], y=df['SMA20'],
                             mode='lines', name='SMA 20',
                             line=dict(color='yellow', width=1)), row=1, col=1)

    # C. Prediction Marker (Tomorrow)
    fig.add_trace(go.Scatter(x=[tomorrow_date], y=[predicted_close],
                             mode='markers+text', name='Prediction',
                             marker=dict(color='cyan', size=15, symbol='star'),
                             text=[f"{predicted_close:.1f}"], textposition="top center"), row=1, col=1)

    # D. Prediction Range (Error Bars)
    fig.add_trace(go.Scatter(x=[tomorrow_date, tomorrow_date], 
                             y=[predicted_low, predicted_high],
                             mode='lines', name='Pred Range',
                             line=dict(color='cyan', width=4)), row=1, col=1)

    # E. Volume Bar Chart
    colors = ['red' if row['Open'] - row['Close'] >= 0 else 'green' for index, row in df.iterrows()]
    fig.add_trace(go.Bar(x=df['Date'], y=df['Volume'], name='Volume', marker_color=colors), row=2, col=1)

    # ** RSI Chart **
    fig.add_trace(go.Scatter(x=df['Date'], y=df['RSI'], name='RSI', 
                             line=dict(color='#ff00ff', width=2)), row=3, col=1)
    
    # RSI Reference Lines (70 and 30)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)
    fig.add_hrect(y0=30, y1=70, fillcolor="gray", opacity=0.1, line_width=0, row=3, col=1)

    # --- F. DASHBOARD LAYOUT (Web Design) ---
    last_close = df['Close'].iloc[-1]
    change = last_close - df['Close'].iloc[-2]
    pct_change = (change / df['Close'].iloc[-2]) * 100
    color_change = "green" if change >= 0 else "red"

    dashboard_title = (
        f"<b>{symbol}</b>: ₹{last_close:.2f} "
        f"<span style='color:{color_change}'>({change:+.2f} / {pct_change:+.2f}%)</span><br>"
        f"<span style='font-size: 14px; color: gray'>Mood: {avg_sentiment:.3f} | RSI: {current_rsi:.1f}</span>"
    )

    fig.update_layout(
        title=dashboard_title,
        yaxis_title='Price (INR)',
        template='plotly_dark', # Dark Mode
        height=900,
        showlegend=False,
        hovermode="x unified"
    )

    # --- PART 5: ADD TEXT REPORT TO HTML ---
    # Determine RSI Status Text
    rsi_status = "Neutral"
    rsi_color = "white"
    if current_rsi > 70:
        rsi_status = "Overbought (High Risk)"
        rsi_color = "red"
    elif current_rsi < 30:
        rsi_status = "Oversold (Bounce Likely)"
        rsi_color = "green"

    html_content = f"""
<html>
<head><style>
body{{font-family: sans-serif; background-color: #111; color: #ddd; text-align: center;}}
.box{{display: inline-block; background: #222; padding: 20px; margin: 10px; border-radius: 10px; border: 1px solid #444; vertical-align: top; width: 300px;}}
h2{{color: #00ccff;}} .pos{{color: #00ff00;}} .neg{{color: #ff3333;}}
.selector{{padding: 20px; background: #222; border-radius: 10px; margin: 20px; border: 2px solid #00ccff;}}
select{{padding: 10px; font-size: 16px; border-radius: 5px; background: #111; color: #0ff; border: 1px solid #0ff; cursor: pointer;}}
input{{padding: 10px; font-size: 16px; border-radius: 5px; background: #111; color: #0ff; border: 1px solid #0ff; width: 200px;}}
button{{padding: 10px 20px; margin-left: 10px; font-size: 16px; border-radius: 5px; background: #00ccff; color: #111; border: none; cursor: pointer; font-weight: bold;}}
button:hover{{background: #00ffff;}}
</style></head>
<body>
    <div class="selector">
        <h1>🤖 Advanced AI Stock Dashboard</h1>
        <h3 style="color: #00ccff;">📊 Current Stock: <b>{symbol}</b></h3>
        
        <form method="GET" action="/" style="margin-bottom: 20px;">
            <label for="symbol" style="font-size: 18px; color: #00ccff;"><b>Select from Common Stocks:</b></label><br><br>
            <select name="symbol" id="symbol">
                <option value="" disabled selected>-- Choose a stock --</option>
                {''.join([f'<option value="{s}">{s}</option>' for s in COMMON_STOCKS])}
            </select>
            <button type="submit">Analyze</button>
        </form>
        
        <hr style="border: 1px solid #444; width: 50%;">
        
        <form method="GET" action="/">
            <label style="font-size: 18px; color: #00ccff;"><b>Or Search Custom Stock:</b></label><br><br>
            <input type="text" name="symbol" placeholder="e.g., ADANIGREEN, TATAMOTORS" required>
            <button type="submit">Search</button>
        </form>
    </div>

    <h2 style="color: #00ccff; margin-top: 40px;">📊 Technical & AI Analysis</h2>
    
    <div class="box">
        <h2>📅 Market Data</h2>
        <p><b>Date:</b> {last_date.date()}</p>
        <p><b>Close:</b> ₹{last_close:.2f}</p>
        <p><b>Vol:</b> {int(df['Volume'].iloc[-1]/1000)}k</p>
        <p style="border-top: 1px solid #555; padding-top: 10px;">
           <b>RSI (14):</b> <span style="color: {rsi_color}">{current_rsi:.1f}</span><br>
           <small>{rsi_status}</small>
        </p>
    </div>

    <div class="box">
        <h2>🚀 AI Prediction</h2>
        <p><b>Target Date:</b> {tomorrow_date.date()}</p>
        <p style="font-size: 24px; font-weight: bold; color: cyan;">Target: ₹{predicted_close:.2f}</p>
        <p><b>Likely Range:</b><br> ₹{predicted_low:.2f} — ₹{predicted_high:.2f}</p>
        <p><i>(News: {avg_sentiment:.2f} | RSI Adj: {rsi_factor})</i></p>
    </div>

    <div class="box" style="width: 600px; text-align: left;">
        <h2>📰 Market Sentiment (Live)</h2>
        <ul style="font-size: 13px; line-height: 1.6;">
            {''.join([f'<li>{h}</li>' for h in latest_headlines]) if latest_headlines else '<li>No relevant news found</li>'}
        </ul>
    </div>
</body>
</html>
"""

    chart_html = fig.to_html(include_plotlyjs='cdn')
    final_report = chart_html.replace("<body>", "<body>" + html_content)
    
    return final_report


# --- FLASK WEB ROUTES ---
@app.route('/')
def dashboard():
    """Main dashboard route"""
    symbol = request.args.get('symbol', DEFAULT_STOCK).upper().strip()
    
    # Validate symbol
    if not symbol:
        symbol = DEFAULT_STOCK
    
    result = generate_dashboard(symbol)
    
    if result is None:
        return f"""
        <html>
        <head><style>body{{background: #111; color: #ddd; font-family: sans-serif; text-align: center;}}</style></head>
        <body>
        <h1 style="color: #ff3333;">❌ Error: Stock '{symbol}' not found</h1>
        <p>We could not retrieve data for this stock. It may be delisted, paused, or the ticker is incorrect.</p>
        <p><b>Tip:</b> Try searching for just the name, e.g., 'RELIANCE' instead of 'RELIANCE.NS'.</p>
        <p><a href="/" style="color: #00ccff; font-size: 18px;">← Go Back to Dashboard</a></p>
        </body>
        </html>
        """
    
    return result

if __name__ == '__main__':
    print("\n" + "="*50)
    print("🚀 Starting Advanced AI Dashboard Server...")
    print("📍 Open http://127.0.0.1:5000 in your browser")
    print("="*50 + "\n")
    app.run(debug=True, port=5000)