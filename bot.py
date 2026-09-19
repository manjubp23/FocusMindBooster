import logging
import sqlite3
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# टोकन और लिंक (इन्हें बदलें)
BOT_TOKEN = "8849310737:AAGTM36B4xQ_DX3JESjQgeCTO4NniuMWFDM" 
MEDITATION_LINK = "https://your-meditation-program-link.com" 

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def init_db():
    conn = sqlite3.connect('referrals.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            referred_by INTEGER,
            referral_count INTEGER DEFAULT 0,
            unlocked INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args
    
    conn = sqlite3.connect('referrals.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    
    if not user:
        referrer_id = None
        if args and args.isdigit():
            referrer_id = int(args)
            if referrer_id == user_id:
                referrer_id = None
        
        cursor.execute("INSERT INTO users (user_id, referred_by) VALUES (?, ?)", (user_id, referrer_id))
        conn.commit()
        
        if referrer_id:
            cursor.execute("SELECT referral_count, unlocked FROM users WHERE user_id = ?", (referrer_id,))
            referrer = cursor.fetchone()
            if referrer:
                new_count = referrer[0] + 1
                cursor.execute("UPDATE users SET referral_count = ? WHERE user_id = ?", (new_count, referrer_id))
                conn.commit()
                
                try:
                    await context.bot.send_message(
                        chat_id=referrer_id, 
                        text=f"🎉 किसी ने आपके लिंक से ज्वाइन किया है! आपके कुल रेफ़रल: {new_count}/2"
                    )
                    if new_count >= 2 and referrer[1] == 0:
                        cursor.execute("UPDATE users SET unlocked = 1 WHERE user_id = ?", (referrer_id,))
                        conn.commit()
                        await context.bot.send_message(
                            chat_id=referrer_id, 
                            text=f"🥳 बधाई हो! आपके 2 रेफ़रल पूरे हो गए हैं। आपका मेडिटेशन प्रोग्राम अनलॉक हो गया है:\n\n{MEDITATION_LINK}"
                        )
                except Exception as e:
                    logging.error(f"Error sending message: {e}")

    bot_info = await context.bot.get_me()
    referral_link = f"https://t.me{bot_info.username}?start={user_id}"
    
    cursor.execute("SELECT referral_count, unlocked FROM users WHERE user_id = ?", (user_id,))
    current_user = cursor.fetchone()
    
    welcome_text = (
        f"नमस्ते {update.effective_user.first_name}!\n\n"
        f"🧘 स्पेशल मेडिटेशन प्रोग्राम अनलॉक करने के लिए आपको **2 लोगों** को इस बॉट पर जोड़ना होगा।\n\n"
        f"🔗 आपका यूनिक रेफ़रल लिंक:\n{referral_link}\n\n"
        f"📊 आपके वर्तमान रेफ़रल: {current_user[0] if current_user else 0}/2"
    )
    
    if current_user and current_user[1] == 1:
        welcome_text += f"\n\n🎁 आपका प्रोग्राम अनलॉक है: {MEDITATION_LINK}"
        
    await update.message.reply_text(welcome_text, parse_mode="Markdown")
    conn.close()

def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    print("बॉट शुरू हो गया है...")
    
    # Render फ्री सर्वर के लिए वेबहुक सेटअप
    port = int(os.environ.get("PORT", 8080))
    app.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=BOT_TOKEN,
        webhook_url=f"https://onrender.com{BOT_TOKEN}"
    )

if __name__ == '__main__':
    main()
