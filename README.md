# 🤖 Stock Analysis Dashboard

A cross-platform Flask web application for real-time stock analysis, sentiment analysis, and price predictions using AI/ML.

## ✨ Features

- 📊 **Interactive Charts** - Candlestick charts with trend lines
- 🤖 **Price Prediction** - ML-based price forecasting
- 📰 **Sentiment Analysis** - Live news sentiment scoring
- 🌐 **Web-Based Selection** - Easy stock selection from dropdown or custom search
- 📱 **Cross-Platform** - Works on Windows, macOS, and Linux
- 🔄 **Real-Time Data** - Live market data from Yahoo Finance
- 🎯 **Prediction Range** - High/Low targets with news adjustment

## 📋 Requirements

- **Python 3.7+**
- **Internet Connection** (for market data and news)

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)

**On Linux/macOS:**
```bash
chmod +x run.sh setup.py
python3 setup.py
./run.sh
```

**On Windows:**
```cmd
python setup.py
run.bat
```

### Option 2: Manual Setup

1. **Install Python 3.7+** from [python.org](https://www.python.org)

2. **Clone or download this project**

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   
   **Linux/macOS:**
   ```bash
   python3 app.py
   ```
   
   **Windows:**
   ```cmd
   python app.py
   ```

5. **Open in browser:**
   - Local: `http://127.0.0.1:5000`
   - Network: `http://<your-ip>:5000`

## 📖 Usage

1. **Select a Stock:**
   - Choose from 15 popular Indian stocks (dropdown menu)
   - Or search for any stock symbol

2. **View Analysis:**
   - Current price and change percentage
   - Interactive candlestick chart
   - Volume analysis
   - Market sentiment score

3. **Check Prediction:**
   - Tomorrow's target price
   - High/Low range
   - News sentiment impact

4. **Read News:**
   - Latest headlines for the stock
   - Sentiment indicators (🟢 🔴 ⚪)

## 🌐 Network Access

To access from another device on your network:

1. Find your computer's IP address:
   
   **Linux/macOS:**
   ```bash
   ifconfig | grep "inet "
   ```
   
   **Windows:**
   ```cmd
   ipconfig
   ```

2. Open in another device's browser:
   ```
   http://<your-computer-ip>:5000
   ```

## 📦 Included Stocks

- TCS, INFY, WIPRO, HCL (IT)
- RELIANCE, HDFC (Banking/Finance)
- SBIN, ICICIBANK, BAJAJFINSV
- ADANIPORTS, MARUTI, COAL
- NTPC, POWERGRID
- IRB (Default)

## 🔧 Configuration

**Change default port:**
```bash
PORT=8000 python app.py
```

**Custom stock:**
Use the search box to enter any NSE/BSE symbol

## 📁 File Structure

```
Stock/
├── app.py                 # Main Flask application
├── setup.py              # Setup script
├── requirements.txt      # Python dependencies
├── run.sh               # Linux/macOS runner
├── run.bat              # Windows runner
├── README.md            # This file
└── web_dashboard.py     # Legacy (deprecated)
```

## ⚠️ Troubleshooting

**"Module not found" error:**
```bash
pip install -r requirements.txt
```

**Port already in use:**
```bash
PORT=8000 python app.py
```

**NLTK data missing:**
The app auto-downloads VADER sentiment data on first run

**Network access not working:**
- Check firewall settings
- Ensure running on `0.0.0.0` (default)
- Check IP address is correct

## 🛠️ Development

To modify the app:

1. Edit `app.py`
2. Restart the application
3. Changes take effect immediately (debug mode)

## 📊 API Endpoints

- `GET /` - Main dashboard
- `GET /api/stocks` - List of available stocks
- `GET /health` - Health check

## 📝 Notes

- Data is fetched from Yahoo Finance
- News is fetched from Google News RSS
- Sentiment analysis uses VADER (NLTK)
- Predictions are based on Linear Regression
- All calculations are real-time

## ⚖️ License

Free to use for personal and educational purposes.

## 💡 Tips

- Market data updates during trading hours
- Predictions are estimates based on trends
- Check multiple sources before trading
- Use for educational purposes

## 🤝 Support

If you encounter issues:

1. Check Python version: `python --version`
2. Verify internet connection
3. Check if port 5000 is available
4. See NLTK section if sentiment analysis fails

---

**Enjoy your stock analysis dashboard! 📈**
