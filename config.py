# config.py

# أولاً: إعدادات Telegram API
# يرجى استبدال القيم التالية بالقيم الصحيحة التي تم الحصول عليها من my.telegram.org
# API_ID: 2123456 (مثال)
# API_HASH: 'cf389dadecdf3fac0aff0fb5c93f1f8b' (مثال)
# تم استخراج API_HASH من الصورة المرفقة: cf389dadecdf3fac0aff0fb5c93f1f8b
# يجب على المستخدم تزويدنا بـ API_ID الخاص به.

# ملاحظة: يجب على المستخدم إدخال API_ID الخاص به
API_ID = 23933005
API_HASH = 'cf389dadecdf3fac0aff0fb5c93f1f8b'

# ثانياً: إعدادات قاعدة البيانات
# نستخدم SQLite كقاعدة بيانات افتراضية لسهولة الإعداد
DATABASE_URL = "sqlite:///price_monitor.db"

# ثالثاً: إعدادات البوت
# معرف المستخدم الخاص بك (لإرسال التنبيهات). يمكن الحصول عليه من @userinfobot
ADMIN_USER_ID = 3288

# رابعاً: إعدادات المقارنة
# الفترة الزمنية للمقارنة (بالثواني). 86400 ثانية = 24 ساعة
COMPARISON_WINDOW_SECONDS = 86400 

# خامساً: إعدادات استخلاص المعلومات (NLP)
# اسم نموذج AraBERT الذي سيتم استخدامه
ARABERT_MODEL_NAME = "aubmindlab/bert-base-arabertv02"
