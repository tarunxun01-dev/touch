import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import sqlite3
import threading
import time
import random
from flask import Flask
import os

# ==========================================
#             CONFIGURATION
# ==========================================
BOT_TOKEN = "8401447636:AAEEB_WQ7yjzlGxldcyNfTFQezOYcXFsAeE"
ADMIN_ID = 8306147833
FORCE_CHANNEL = "@LEAKMETHODFREE"
REDIRECT_USER = "@ALOKLOOTOFFER"
DB_CHANNEL = "@coinsotp"  # Yahan backup aayega

bot = telebot.TeleBot(BOT_TOKEN)

# ==========================================
#             FLASK WEB SERVER
# ==========================================
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running 24/7 on Render!"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    t = threading.Thread(target=run_web_server)
    t.start()

# ==========================================
#             DATABASE SETUP
# ==========================================
conn = sqlite3.connect('bot_data.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users
                  (user_id INTEGER PRIMARY KEY, refers INTEGER DEFAULT 0, invited_by INTEGER)''')
conn.commit()

# ==========================================
#             BACKUP FUNCTION
# ==========================================
def backup_db():
    """Takes database file and sends it to the private channel."""
    try:
        with open('bot_data.db', 'rb') as f:
            bot.send_document(DB_CHANNEL, f, caption="🔄 Auto-Backup Completed")
    except Exception as e:
        print(f"Backup failed: {e}")

# ==========================================
#             HELPER FUNCTIONS
# ==========================================
def check_join(user_id):
    try:
        status = bot.get_chat_member(FORCE_CHANNEL, user_id).status
        return status in ['member', 'administrator', 'creator']
    except Exception as e:
        return False

def add_user(user_id, inviter_id=None):
    cursor.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (user_id, invited_by) VALUES (?, ?)", (user_id, inviter_id))
        conn.commit()
        
        if inviter_id:
            cursor.execute("SELECT user_id FROM users WHERE user_id=?", (inviter_id,))
            if not cursor.fetchone():
                cursor.execute("INSERT INTO users (user_id, refers) VALUES (?, 1)", (inviter_id,))
            else:
                cursor.execute("UPDATE users SET refers = refers + 1 WHERE user_id=?", (inviter_id,))
            conn.commit()
            backup_db() # 👈 COIN ADD HUA, BACKUP BHEJ DIYA
            
            try:
                bot.send_message(inviter_id, "🎉 NEW REFERRAL!\nKisi ne aapke link se join kiya hai. +1 Coin Added!")
            except Exception as e:
                pass

# ==========================================
#          HOURLY FAKE BROADCAST
# ==========================================
def hourly_broadcast():
    while True:
        time.sleep(3600)
        cursor.execute("SELECT user_id FROM users")
        users = cursor.fetchall()
        fake_msgs = [
            "🔥 LIVE UPDATE: Ek aur user ne abhi 40 Coins Wala Pack claim kiya hai!",
            "🚀 BOOM! Kisi ne just 80 Coins Wala VIP Pack unlock kar liya!",
            "🏆 CONGRATS: Ek user ne 40 Refers complete kar liye!"
        ]
        msg = random.choice(fake_msgs)
        for u in users:
            try:
                bot.send_message(u[0], msg)
            except:
                pass

threading.Thread(target=hourly_broadcast, daemon=True).start()

# ==========================================
#             START COMMAND
# ==========================================
@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = message.chat.id
    inviter_id = None
    parts = message.text.split()
    
    if len(parts) > 1:
        try:
            inviter_id = int(parts[1])
            if inviter_id == user_id:
                inviter_id = None 
        except ValueError:
            pass

    add_user(user_id, inviter_id)

    if not check_join(user_id):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{FORCE_CHANNEL[1:]}"))
        markup.add(InlineKeyboardButton("✅ Joined (Check)", callback_data="check_join"))
        bot.send_message(user_id, f"🛑 Bot Use Karne Ke Liye Pehle Channel Join Karein!\n\nChannel: {FORCE_CHANNEL}", reply_markup=markup)
        return

    main_menu(message.chat.id)

# ==========================================
#             MAIN MENU UI
# ==========================================
def main_menu(chat_id):
    cursor.execute("SELECT refers FROM users WHERE user_id=?", (chat_id,))
    result = cursor.fetchone()
    refers = result[0] if result else 0

    text = f"""
🤖 Welcome to the Premium OTP Panel Bot! 🤖

🔥 Loot Offers Available:
🎁 40 Coins (Refers): Get 2 Premium OTP Panel APKs!
💎 80 Coins (Refers): Get 5 Premium OTP Panel APKs + VIP Support!

👤 Your Total Coins: {refers}

👇 Niche diye gaye buttons se option select karein:
"""
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(
        KeyboardButton("🔗 Refer & Earn (My Link)"),
        KeyboardButton("🎁 Claim 40 Coin Pack"),
        KeyboardButton("💎 Claim 80 Coin Pack")
    )
    bot.send_message(chat_id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "check_join")
def callback_handler(call):
    user_id = call.message.chat.id
    if check_join(user_id):
        bot.delete_message(user_id, call.message.message_id)
        main_menu(user_id)
    else:
        bot.answer_callback_query(call.id, "❌ Aapne abhi tak channel join nahi kiya hai!", show_alert=True)

# ==========================================
#      BOTTOM KEYBOARD BUTTONS LOGIC
# ==========================================
@bot.message_handler(content_types=['text'])
def handle_menu_buttons(message):
    user_id = message.chat.id
    text = message.text

    if text.startswith('/'):
        return

    if not check_join(user_id):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{FORCE_CHANNEL[1:]}"))
        markup.add(InlineKeyboardButton("✅ Joined (Check)", callback_data="check_join"))
        bot.send_message(user_id, f"🛑 Bot Use Karne Ke Liye Pehle Channel Join Karein!", reply_markup=markup)
        return

    cursor.execute("SELECT refers FROM users WHERE user_id=?", (user_id,))
    result = cursor.fetchone()
    current_coins = result[0] if result else 0

    if "Refer & Earn" in text:
        bot_info = bot.get_me()
        ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
        msg = f"🔗 Your Personal Referral Link:\n{ref_link}\n\n💰 Current Coins: {current_coins}"
        bot.send_message(user_id, msg)

    elif "Claim 40" in text or "Claim 80" in text:
        req_coins = 40 if "Claim 40" in text else 80

        if current_coins < req_coins:
            pending_coins = req_coins - current_coins
            alert_msg = f"❌ INSUFFICIENT BALANCE! ❌\nRequired: {req_coins} | Pending: {pending_coins} ⚠️"
            bot.send_message(user_id, alert_msg)
            return

        cursor.execute("UPDATE users SET refers = refers - ? WHERE user_id = ?", (req_coins, user_id))
        conn.commit()
        backup_db() # 👈 COIN KATE, BACKUP BHEJ DIYA

        bot.send_message(user_id, "⏳ Checking Server Availability...")
        time.sleep(2) 

        error_msg = f"⚠️ 𝗦𝗘𝗥𝗩𝗘𝗥 𝗘𝗥𝗥𝗢𝗥 𝟰𝟬𝟰! ⚠️\nAdmin ko message karein: {REDIRECT_USER}"
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📩 Message Admin For App", url=f"https://t.me/{REDIRECT_USER[1:]}"))
        bot.send_message(user_id, error_msg, reply_markup=markup)

# ==========================================
#             ADMIN COMMANDS
# ==========================================
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.chat.id == ADMIN_ID:
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        text = f"👑 ADMIN PANEL 👑\n👥 Total Users: {total_users}\n/broadcast <msg>\n/addrefer <id> <amount>"
        bot.send_message(ADMIN_ID, text)

@bot.message_handler(commands=['addrefer'])
def admin_add_refer(message):
    if message.chat.id == ADMIN_ID:
        try:
            parts = message.text.split()
            target_user = int(parts[1])
            amount = int(parts[2])
            cursor.execute("UPDATE users SET refers = refers + ? WHERE user_id = ?", (amount, target_user))
            conn.commit()
            backup_db() # 👈 ADMIN NE COIN ADD KIYE, BACKUP BHEJ DIYA
            bot.send_message(ADMIN_ID, f"✅ Successfully added {amount} coins to User ID: {target_user}")
        except Exception as e:
            bot.send_message(ADMIN_ID, "❌ Galat Format!")

@bot.message_handler(commands=['broadcast'])
def admin_broadcast(message):
    if message.chat.id == ADMIN_ID:
        msg_text = message.text.replace('/broadcast ', '')
        cursor.execute("SELECT user_id FROM users")
        users = cursor.fetchall()
        for u in users:
            try:
                bot.send_message(u[0], f"📢 ADMIN MESSAGE:\n\n{msg_text}")
            except:
                pass
        bot.send_message(ADMIN_ID, "✅ Broadcast Done!")

# ==========================================
#       RESTORE DATABASE FROM CHANNEL
# ==========================================
@bot.message_handler(content_types=['document'])
def restore_db(message):
    if message.chat.id == ADMIN_ID and message.document.file_name == 'bot_data.db':
        try:
            bot.send_message(ADMIN_ID, "⏳ Restoring Database...")
            file_info = bot.get_file(message.document.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            
            with open('bot_data.db', 'wb') as new_file:
                new_file.write(downloaded_file)
            
            bot.send_message(ADMIN_ID, "✅ Database Restored Successfully! Sab data wapas aa gaya.")
        except Exception as e:
            bot.send_message(ADMIN_ID, f"❌ Restore Failed: {e}")

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()
