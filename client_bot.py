# client_bot.py
import asyncio
from telethon import TelegramClient, events
from telethon.tl.types import PeerUser
import os
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from config import API_ID, API_HASH, ADMIN_USER_ID, COMPARISON_WINDOW_SECONDS
from database import init_db, PriceEntry, SessionLocal
from extraction_logic import extract_price_data

# تهيئة قاعدة البيانات
init_db()

# تهيئة عميل Telegram
# نستخدم اسم جلسة "price_analysis_ses" كما ورد في متطلبات Git Cleanup
client = TelegramClient('price_analysis_ses', API_ID, API_HASH)

# قائمة القنوات التي يجب مراقبتها (يمكن إضافتها لاحقاً عبر أمر في البوت)
# يجب أن تكون معرفات القنوات (IDs) أو أسماء المستخدمين (@usernames)
MONITORED_CHANNELS = load_monitored_channels() 

# دالة مساعدة لتخزين البيانات في قاعدة البيانات
def save_price_entry(product_name, price, currency, channel_name, channel_id, message_id, raw_text):
    db: Session = SessionLocal()
    try:
        entry = PriceEntry(
            product_name=product_name,
            price=price,
            currency=currency,
            post_date=datetime.utcnow(),
            channel_name=channel_name,
            channel_id=channel_id,
            message_id=message_id,
            raw_text=raw_text
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry
    except Exception as e:
        print(f"Error saving to DB: {e}")
        db.rollback()
        return None
    finally:
        db.close()

# دالة منطق المقارنة والتنبيه (Phase 4)
async def check_for_best_deal(new_entry: PriceEntry):
    if not new_entry:
        return

    db: Session = SessionLocal()
    try:
        # 1. تحديد فترة المقارنة
        time_threshold = datetime.utcnow() - timedelta(seconds=COMPARISON_WINDOW_SECONDS)

        # 2. البحث عن أقل سعر لنفس المنتج خلال الفترة الزمنية المحددة
        best_deal = db.query(PriceEntry) \
            .filter(PriceEntry.product_name == new_entry.product_name) \
            .filter(PriceEntry.post_date >= time_threshold) \
            .order_by(PriceEntry.price.asc()) \
            .first()

        # 3. التحقق مما إذا كانت الرسالة الجديدة هي أفضل صفقة
        if best_deal and best_deal.id == new_entry.id:
            # تم العثور على أفضل صفقة، وإرسال تنبيه
            if ADMIN_USER_ID != 0:
                message = (
                    f"🚨 **تنبيه: أفضل صفقة تم اكتشافها!** 🚨\n\n"
                    f"**المنتج:** {new_entry.product_name}\n"
                    f"**السعر:** {new_entry.price} {new_entry.currency}\n"
                    f"**القناة:** {new_entry.channel_name}\n"
                    f"**تاريخ النشر:** {new_entry.post_date.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                    f"هذا هو أقل سعر تم رصده خلال الـ {COMPARISON_WINDOW_SECONDS // 3600} ساعة الماضية."
                )
                await client.send_message(PeerUser(ADMIN_USER_ID), message)
                print(f"Alert sent for best deal: {new_entry.product_name} at {new_entry.price}")
            else:
                print("ADMIN_USER_ID is not set. Cannot send alert.")

    except Exception as e:
        print(f"Error in check_for_best_deal: {e}")
    finally:
        db.close()

# معالج الرسائل الجديدة
@client.on(events.NewMessage(chats=MONITORED_CHANNELS))
async def handler_new_message(event):
    message_text = event.message.message
    
    # 1. استخلاص البيانات
    product_name, price, currency = extract_price_data(message_text)
    
    if product_name and price is not None:
        # 2. تخزين البيانات
        chat = await event.get_chat()
        channel_name = getattr(chat, 'title', 'Unknown Channel')
        channel_id = chat.id
        message_id = event.message.id
        
        new_entry = save_price_entry(
            product_name, 
            price, 
            currency, 
            channel_name, 
            channel_id, 
            message_id, 
            message_text
        )
        
        print(f"Saved: {product_name} - {price} {currency} from {channel_name}")
        
        # 3. المقارنة والتنبيه
        await check_for_best_deal(new_entry)
    else:
        # print(f"Skipped message (no price found): {message_text[:50]}...")
        pass

# دالة مساعدة لقراءة القنوات من الملف
def load_monitored_channels():
    channels = []
    file_path = os.path.join(os.path.dirname(__file__), 'channels.txt')
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    # استخراج اسم المستخدم أو الرابط
                    if line.startswith('http'):
                        # Telethon يمكنه التعامل مع الروابط
                        channels.append(line)
                    elif line.startswith('@'):
                        channels.append(line)
                    else:
                        # افتراض أنه اسم مستخدم
                        channels.append(f'@{line}')
        print(f"Loaded {len(channels)} channels for monitoring.")
    except FileNotFoundError:
        print("channels.txt not found. Monitoring list is empty.")
    return channels

# دالة بدء التشغيل
async def main():
    print("Connecting to Telegram...")
    # يجب على المستخدم إدخال رقم هاتفه لتسجيل الدخول لأول مرة
    await client.start()
    print("Client is running. Listening for new messages...")
    
    # يمكن إضافة قنوات المراقبة هنا يدوياً إذا لزم الأمر
    # MONITORED_CHANNELS.append('username_of_channel')
    
    await client.run_until_disconnected()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped by user.")
    except Exception as e:
        print(f"An error occurred: {e}")
