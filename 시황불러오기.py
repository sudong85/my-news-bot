import os
import logging
import requests
import re
import sys
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta

# --- [설정 정보] ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN") or "여기에_본인_토큰"
CHAT_ID = os.getenv("CHAT_ID") or "여기에_본인_ID"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def escape_markdown(text: str) -> str:
    special_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(special_chars)}])', r'\\\1', text)

def get_latest_news(count=20):
    url = "https://finance.naver.com/news/mainnews.naver"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'}
    
    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        news_items = soup.select('.mainNewsList .articleSubject a')
        
        found_news = []
        for i, anchor in enumerate(news_items[:count], 1):
            title = anchor.get_text(strip=True)
            raw_link = anchor['href']
            
            aid = re.search(r'article_id=(\d+)', raw_link)
            oid = re.search(r'office_id=(\d+)', raw_link)
            
            if aid and oid:
                clean_link = f"https://n.news.naver.com/mnews/article/{oid.group(1)}/{aid.group(1)}"
                safe_title = escape_markdown(title)
                found_news.append(f"{i}\\. *{safe_title}*\n[👉 본문]({clean_link})")
        
        if found_news:
            KST = timezone(timedelta(hours=9))
            now_str = datetime.now(KST).strftime('%Y\\-%m\\-%d %H:%M')
            return f"📢 실시간 주요 뉴스 TOP {len(found_news)} \\({now_str}\\)\n\n" + "\n\n".join(found_news)
        else:
            return "❓ 현재 업데이트된 뉴스가 없습니다\."
    except Exception as e:
        logging.error(f"뉴스 수집 오류: {e}")
        return f"❌ 오류 발생: {escape_markdown(str(e))}"

def send_telegram(text: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "MarkdownV2",
        "disable_web_page_preview": True
    }
    res = requests.post(url, json=payload, timeout=10)
    res.raise_for_status()
    logging.info("텔레그램 전송 성공")

# ──────────────────────────────────────────
# GitHub Actions 모드 (스케줄 자동 전송)
# ──────────────────────────────────────────
if os.getenv("GITHUB_ACTIONS") == "true":
    print("🤖 GitHub Actions: 정기 배달 모드 실행 중...")
    try:
        send_telegram(get_latest_news(20))
    except Exception as e:
        logging.error(f"실행 오류: {e}")
        sys.exit(1)

# ──────────────────────────────────────────
# 로컬 PC 모드 (텔레그램 메시지 응답 봇)
# ──────────────────────────────────────────
else:
    from telegram import Update
    from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

    print("💻 PC 모드: 텔레그램에 아무 메시지나 입력하면 최신 뉴스를 가져옵니다.")

    async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if str(update.message.chat_id) == CHAT_ID:
            await update.message.reply_text(
                get_latest_news(20),
                parse_mode='MarkdownV2',
                disable_web_page_preview=True
            )

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()
