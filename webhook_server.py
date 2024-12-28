from flask import Flask, request
from binance.client import Client
import requests

response = requests.get('https://api64.ipify.org?format=json')
print("Server Public IP:", response.json()['ip'])

app = Flask(__name__)

# Binance API Bilgileri
api_key = ""
api_secret = ""
client = Client(api_key, api_secret)

# İşlem Yapılacak Coin ve İlk İşlem İçin Kullanılacak USDT
symbol = "LUNAUSDT"
initial_usdt = 100.0

# Mevcut Pozisyon Durumu (None, "LONG", "SHORT")
current_position = None


@app.route('/webhook', methods=['POST'])
def webhook():
    global current_position

    data = request.json
    if not data:
        return {"message": "No data received"}, 400

    action = data.get("action")

    # Mevcut bakiyeyi al
    account_info = client.get_account()
    balances = {bal['asset']: float(bal['free']) for bal in account_info['balances']}
    usdt_balance = balances.get("USDT", 0.0)

    # Piyasa fiyatını al
    ticker = client.get_symbol_ticker(symbol=symbol)
    current_price = float(ticker['price'])

    # İşlem miktarını belirle
    trade_amount_usdt = usdt_balance if usdt_balance > 0 else initial_usdt
    quantity = round(trade_amount_usdt / current_price, 2)  # 2 ondalık basamak

    if action == "exit_long" and current_position == "LONG":
        # Long pozisyonu kapat
        order = client.order_market_sell(symbol=symbol, quantity=quantity)
        current_position = None
        print("Long pozisyon kapatıldı:", order)
        return {"message": "Long pozisyon kapatıldı"}, 200

    elif action == "exit_short" and current_position == "SHORT":
        # Short pozisyonu kapat
        order = client.order_market_buy(symbol=symbol, quantity=quantity)
        current_position = None
        print("Short pozisyon kapatıldı:", order)
        return {"message": "Short pozisyon kapatıldı"}, 200

    elif action == "long" and current_position is None:
        # Yeni Long pozisyon aç
        order = client.order_market_buy(symbol=symbol, quantity=quantity)
        current_position = "LONG"
        print("Long pozisyon açıldı:", order)
        return {"message": "Long pozisyon açıldı"}, 200

    elif action == "short" and current_position is None:
        # Yeni Short pozisyon aç
        order = client.order_market_sell(symbol=symbol, quantity=quantity)
        current_position = "SHORT"
        print("Short pozisyon açıldı:", order)
        return {"message": "Short pozisyon açıldı"}, 200

    return {"message": "Geçersiz işlem türü veya mevcut pozisyon uyuşmazlığı"}, 400


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
