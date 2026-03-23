import os
import logging
import requests
import re
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from datetime import datetime

# --- [하이브리드 설정: PC & GitHub 공용] ---
# GitHub 금고(Secrets)에서 가져오되, 없으면 내 PC용 토큰을 직접 사용합니다.
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN") or "8789285993:AAH8chpk0xU_TniwibdlyVM8tnqLwp-iN3I"
CHAT_ID = os.getenv("CHAT_ID") or "610199821"
# ------------------------------------------

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
            
            # 기사 ID 추출 및 표준 주소 생성
            aid = re.search(r'article_id=(\d+)', raw_link)
            oid = re.search(r'office_id=(\d+)', raw_link)
            
            if aid and oid:
                clean_link = f"https://n.news.naver.com/mnews/article/{oid.group(1)}/{aid.group(1)}"
                if search_word in title:
                    found_news.append(f"📍 *{title}*\n[👉 본문 읽기]({clean_link})")
        
        if found_news:
            return f"🚀 '{search_word}' 결과 ({len(found_news)}건 / 100개 분석)\n\n" + "\n\n".join(found_news)
        else:
            return f"❓ 최근 100개 뉴스 중 '{search_word}' 관련 기사가 없습니다."
    except Exception as e:
        return f"❌ 시스템 오류: {e}"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.message.chat_id) == CHAT_ID:
        user_text = update.message.text
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 요청 처리: {user_text}")
        await update.message.reply_text(get_naver_news(user_text), parse_mode='Markdown', disable_web_page_preview=True)

if __name__ == '__main__':
    # GitHub Actions 환경(스케줄러)에서는 한 번만 실행하고 종료해야 합니다.
    # 만약 사용자가 '뉴스'라고 직접 치는 대신, 자동으로 매번 결과를 받고 싶다면 아래 로직을 씁니다.
    
    # 1. GitHub에서 '자동 실행' 시 (인자값이 없는 경우 예시로 활용 가능)
    if os.getenv("GITHUB_ACTIONS") == "true":
        print("🤖 GitHub Actions 모드로 자동 뉴스를 수집합니다.")
        # 자동으로 '증시' 키워드 뉴스를 긁어서 나에게 전송
        import asyncio
        from telegram import Bot
        async def send_auto_news():
            bot = Bot(token=TELEGRAM_TOKEN)
            await bot.send_message(chat_id=CHAT_ID, text=get_naver_news("증시"), parse_mode='Markdown')
        asyncio.run(send_auto_news())
    
    # 2. 내 PC에서 '대화형'으로 실행 시
    else:
        print("💻 PC 모드: 텔레그램 메시지를 기다립니다...")
        app = ApplicationBuilder().token
