import os
import asyncio
import ccxt
import pandas as pd
import numpy as np
from telegram import Bot
from telegram.constants import ParseMode

BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')

# Setup Binance Futures
exchange = ccxt.binance({
    'enableRateLimit': True,
    'options': {'defaultType': 'future'}
})

def get_data(symbol, timeframe='5m', limit=100):
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df

def calculate_indicators(df):
    df['ema9'] = df['close'].ewm(span=9).mean()
    df['ema21'] = df['close'].ewm(span=21).mean()
    df['rsi'] = compute_rsi(df['close'], 14)
    df['volume_ma'] = df['volume'].rolling(20).mean()
    return df

def compute_rsi(series, period):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def generate_signal(df, symbol):
    last = df.iloc[-1]
    prev = df.iloc[-2]
    
    # EMA Cross
    ema_bull = last['ema9'] > last['ema21'] and prev['ema9'] <= prev['ema21']
    ema_bear = last['ema9'] < last['ema21'] and prev['ema9'] >= prev['ema21']
    
    # RSI Divergence simple
    rsi_oversold = last['rsi'] < 30
    rsi_overbought = last['rsi'] > 70
    
    # Volume Spike
    vol_spike = last['volume'] > last['volume_ma'] * 1.5
    
    direction = None
    reason = ""
    confidence = 0
    
    if ema_bull and rsi_oversold and vol_spike:
        direction = "LONG"
        reason = "EMA Bull Cross + RSI Oversold + Volume Spike"
        confidence = 85
    elif ema_bear and rsi_overbought and vol_spike:
        direction = "SHORT"
        reason = "EMA Bear Cross + RSI Overbought + Volume Spike"
        confidence = 85
    
    if direction:
        current_price = last['close']
        entry_low = current_price * 0.997  # 0.3% below
        entry_high = current_price * 1.003
        sl = current_price * 0.985 if direction == "LONG" else current_price * 1.015
        tp1 = current_price * 1.007 if direction == "LONG" else current_price * 0.993
        tp2 = current_price * 1.014
        tp3 = current_price * 1.023
        tp4 = current_price * 1.038
        risk = 1.5  # %
        
        signal = {
            'direction': direction,
            'symbol': symbol,
            'entry_low': round(entry_low, 2),
            'entry_high': round(entry_high, 2),
            'tp1': round(tp1, 2),
            'tp2': round(tp2, 2),
            'tp3': round(tp3, 2),
            'tp4': round(tp4, 2),
            'sl': round(sl, 2),
            'reason': reason,
            'confidence': confidence,
            'leverage': '10-20x'
        }
        return signal
    return None

async def send_signal(signal):
    bot = Bot(token=BOT_TOKEN)
    message = f"""
🔥 **{signal['direction']} SIGNAL** | {signal['symbol']} Perpetual 🔥

📈 **Entry Zone**: ${signal['entry_low']} – ${signal['entry_high']}
🎯 **TP1**: ${signal['tp1']} (1.5%)
🎯 **TP2**: ${signal['tp2']} (2.5%)
🎯 **TP3**: ${signal['tp3']} (4%)
🎯 **TP4**: ${signal['tp4']} (6%)
🛑 **SL**: ${signal['sl']} (1.5% Risk)

⚡ **Reason**: {signal['reason']}
💪 **Leverage Sugesti**: {signal['leverage']} | Confidence: {signal['confidence']}%

#Futures #CryptoSignals | @YourChannel
    """
    await bot.send_message(chat_id=CHANNEL_ID, text=message.strip(), parse_mode=ParseMode.MARKDOWN)

async def main():
    symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'XRPUSDT']  # Tambah lebih banyak kalau mau
    print("Bot sinyal futures dimulai...")
    
    while True:
        for symbol in symbols:
            try:
                df = get_data(symbol)
                df = calculate_indicators(df)
                signal = generate_signal(df, symbol)
                if signal:
                    await send_signal(signal)
                    print(f"Sinyal {signal['direction']} untuk {symbol} dikirim!")
            except Exception as e:
                print(f"Error {symbol}: {e}")
        
        await asyncio.sleep(300)  # Scan setiap 5 menit

if __name__ == '__main__':
    asyncio.run(main())
