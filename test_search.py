import requests

def get_ticker_from_name(query):
    # If it's likely already a ticker (no spaces, mostly uppercase)
    if " " not in query and sum(1 for c in query if c.isupper()) > len(query) / 2:
        if not (query.endswith('.NS') or query.endswith('.BO')):
            return query.upper() + ".NS"
        return query.upper()
        
    url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}"
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    })
    
    try:
        response = session.get(url, timeout=5)
        data = response.json()
        quotes = data.get('quotes', [])
        
        for quote in quotes:
            symbol = quote.get('symbol', '')
            exchange = quote.get('exchange', '')
            # Prefer NSE and BSE
            if exchange in ['NSI', 'BSE'] or symbol.endswith('.NS') or symbol.endswith('.BO'):
                return symbol
                
        if quotes:
            return quotes[0].get('symbol', '')
            
    except Exception as e:
        print(f"Error: {e}")
        
    # Fallback
    fallback = query.replace(" ", "").upper()
    if not (fallback.endswith('.NS') or fallback.endswith('.BO')):
        return fallback + ".NS"
    return fallback

print(get_ticker_from_name("Tata Motors"))
print(get_ticker_from_name("Reliance"))
print(get_ticker_from_name("Olectra Greentech"))
print(get_ticker_from_name("INFY"))
print(get_ticker_from_name("Zomato"))
