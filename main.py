import os
import re
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

BOT_TOKEN = os.getenv("BOT_TOKEN

def get_token_info(ca):
    # Coba semua chain populer otomatis
    chains = ["solana", "ethereum", "base", "bsc", "arbitrum"]
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    for chain in chains:
        if chain == "solana":
            url = f"https://api.dexscreener.com/latest/dex/pairs/solana/{ca}"
        else:
            url = f"https://api.dexscreener.com/latest/dex/pairs/{chain}/{ca}"
        
        try:
            r = requests.get(url, headers=headers, timeout=8)
            data = r.json()
            if "pair" in data and data["pair"]:
                return data["pair"]
            elif "pairs" in data and data["pairs"]:
                return data["pairs"][0]
        except:
            continue
    return None

def format_message(pair):
    if not pair:
        return "Token tidak ditemukan atau belum listing di DEX mana pun."
    
    b = pair["baseToken"]
    q = pair["quoteToken"]
    p = pair.get("priceUsd", "0")
    pc = pair.get("priceChange", {})
    
    liq = pair.get("liquidity", {}).get("usd", 0)
    fdv = pair.get("fdv", 0)
    vol = pair.get("volume", {}).get("h24", 0)
    
    return f"""
*ANALISIS TOKEN* 

*Token*: {b['symbol']} ({b['name']})
*Address*: `{b['address']}`
*Chain*: {pair['chainId'].title()}

*Harga*: $${float(p):.10f}
*5m*: {pc.get('m5',0)}% | *1h*: {pc.get('h1',0)}% | *24h*: {pc.get('h24',0)}%

*Liquidity*: ${liq:,.0f}
*FDV*: ${fdv:,.0f}
*Volume 24h*: ${vol:,.0f}

{Buka di DexScreener → {pair['url']}
    """.strip()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Halo! Bot Analisis Token GRATIS \n\n"
        "Kirim Contract Address (CA) token apa saja (Solana, ETH, Base, BSC, dll)\n"
        "Contoh:\n"
        "So1eveMent9W1z1Qh7YV7Z9YbS5dX8m5tW1z1Qh7YV7Z9YbS5dX8m5t\n"
        "0x1234567890abcdef1234567890abcdef12345678",
        parse_mode=ParseMode.MARKDOWN
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    # Cari contract address (panjang 32–44 karakter)
    match = re.search(r"[1-9A-HJ-NP-Za-km-z]{32,44}", text)
    if not match:
        await update.message.reply_text("Kirim Contract Address yang valid ya!")
        return
    
    ca = match.group(0)
    msg = await update.message.reply_text("Sedang menganalisis token...")
    
    pair = get_token_info(ca)
    result = format_message(pair)
    
    await msg.edit_text(result, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Bot sedang berjalan...")
    app.run_polling()

if __name__ == '__main__':
    main()
