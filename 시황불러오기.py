import os
import logging
import requests
import re
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from datetime import datetime

# --- [하이브리드 설정] ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN") or "8789285993:AAH8chpk0xU_TniwibdlyVM8tnqLwp-iN3I"
CHAT_ID = os.getenv("CHAT_ID") or "610199821"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def get_naver_news(search_word):
    url = "https://finance.naver.com/news/mainnews.naver"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'}
    
    try:
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')
        news_items = soup.select('.mainNewsList .articleSubject a')
        
        found_news = []
        for anchor in news_items[:100]: # 100개 스캔
            title = anchor.get_text(strip=True)
            raw_link = anchor['href']
            
            aid = re.search(r'article_id=(\d+)', raw_link)
            oid = re.search(r'office_id=(\d+)', raw_link)
            
            if aid and oid:
                clean_link = f"https://n.news.naver.com/mnews/article/{oid.group(1)}/{aid.group(1)}"
                if search_word in title:
                    found_news.append(f"📍 *{title}*\n[👉 본문 읽기]({clean_link})")
        
        if found_news:
            # [Q3 반영] 상위 5개만 슬라이싱하여 시인성 확보
            top_5 = found_news[:5]
            return f"🚀 '{search_word}' 최신 뉴스 5건 (총 {len(found_news)}건 중)\n\n" + "\n\n".join(top_5)
        else:
            return f"❓ 최근 100개 중 '{search_word}' 관련 기사가 없습니다."
    except Exception as e:
        return f"❌ 오류: {e}"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.message.chat_id) == CHAT_ID:
        await update.message.reply_text(get_naver_news(update.message.text), parse_mode='Markdown', disable_web_page_preview=True)

if __name__ == '__main__':
    if os.getenv("GITHUB_ACTIONS") == "true":
        print("🤖 GitHub Actions 모드 실행")
        import asyncio
        from telegram import Bot
        async def send_auto_news():
            bot = Bot(token=TELEGRAM_TOKEN)
            # [Q1 반영] 배달받고 싶은 키워드를 여기서 수정하세요 (예: "증시")
            await bot.send_message(chat_id=CHAT_ID, text=get_naver_news("증시"), parse_mode='Markdown')
        asyncio.run(send_auto_news())
    else:
        print("💻 PC 모드 대기 중...")
        app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
        app.run_polling()
