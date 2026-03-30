import os
import logging
import requests
import re
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from datetime import datetime, timezone, timedelta


# --- [설정 정보] ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN") or "8789285993:AAH8chpk0xU_TniwibdlyVM8tnqLwp-iN3I"
CHAT_ID = os.getenv("CHAT_ID") or "610199821"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def get_latest_news(count=20):
    url = "https://finance.naver.com/news/mainnews.naver"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'}
    
    try:
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')
        news_items = soup.select('.mainNewsList .articleSubject a')
        
        found_news = []
        # [수정] 상위 20개로 확장
        for i, anchor in enumerate(news_items[:count], 1):
            title = anchor.get_text(strip=True)
            raw_link = anchor['href']
            
            aid = re.search(r'article_id=(\d+)', raw_link)
            oid = re.search(r'office_id=(\d+)', raw_link)
            
            if aid and oid:
                clean_link = f"https://n.news.naver.com/mnews/article/{oid.group(1)}/{aid.group(1)}"
                found_news.append(f"{i}. *{title}*\n[👉 본문]({clean_link})")
        
        if found_news:
            KST = timezone(timedelta(hours=9))
            now_str = datetime.now(KST).strftime('%Y-%m-%d %H:%M')
            return f"📢 실시간 주요 뉴스 TOP {len(found_news)} ({now_str})\n\n" + "\n\n".join(found_news)
        else:
            return "❓ 현재 업데이트된 뉴스가 없습니다."
    except Exception as e:
        return f"❌ 오류 발생: {e}"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.message.chat_id) == CHAT_ID:
        # 사용자가 아무 글자나 입력하면 무조건 최신 20개를 쏴줍니다.
        await update.message.reply_text(get_latest_news(20), parse_mode='Markdown', disable_web_page_preview=True)

if __name__ == '__main__':
    if os.getenv("GITHUB_ACTIONS") == "true":
        print("🤖 GitHub Actions: 정기 배달 모드 실행 중...")
        import asyncio
        from telegram import Bot
        async def send_auto_news():
            bot = Bot(token=TELEGRAM_TOKEN)
            await bot.send_message(chat_id=CHAT_ID, text=get_latest_news(20), parse_mode='Markdown')
        asyncio.run(send_auto_news())
    else:
        print("💻 PC 모드: 아무 메시지나 입력하면 최신 뉴스 20개를 가져옵니다.")
        app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
        app.run_polling()
