# extraction_logic.py
import re
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
from config import ARABERT_MODEL_NAME

# تهيئة نموذج AraBERT للتعرف على الكيانات (NER) أو تصنيف النصوص
# ملاحظة: لتبسيط المهمة وتحقيق الهدف الأساسي (استخلاص المنتج والسعر)، سنعتمد بشكل أساسي على Regex
# وسنستخدم AraBERT في المستقبل لتصنيف الرسائل أو تحسين استخلاص اسم المنتج إذا لزم الأمر.

# دالة لاستخلاص السعر والعملة باستخدام التعبيرات النمطية (Regex)
def extract_price_and_currency(text):
    """
    يستخلص السعر والعملة من النص.
    يدعم الأرقام العربية والهندية، وعلامات العملات الشائعة ($، ريال، جنيه، د.إ، إلخ).
    """
    # تحويل الأرقام العربية (الهندية) إلى أرقام إنجليزية لتوحيد المعالجة
    arabic_to_english_digits = str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789')
    text = text.translate(arabic_to_english_digits)

    # تعبير نمطي قوي للبحث عن الأرقام (بما في ذلك الفواصل العشرية) متبوعة أو مسبوقة بعلامة عملة
    # يدعم: 1,200$، 1200 ريال، 1.2k، 1200
    price_regex = re.compile(
        r'(?:(\$|ريال|جنيه|د\.إ|درهم|د\.ك|دينار|يورو|EUR|USD|SAR|EGP)\s*|)(?P<price>\d{1,3}(?:[,\.]\d{3})*(?:[\.,]\d+)?)(?:\s*(?:(\$|ريال|جنيه|د\.إ|درهم|د\.ك|دينار|يورو|EUR|USD|SAR|EGP)|(K|k)))?',
        re.IGNORECASE
    )
    
    matches = list(price_regex.finditer(text))
    
    if not matches:
        return None, None, None

    # نختار التطابق الأخير كونه غالباً ما يكون السعر النهائي للمنتج في نهاية الجملة
    match = matches[-1]
    
    price_str = match.group('price').replace(',', '').replace('.', '') # إزالة الفواصل والنقاط لتنظيف الرقم
    
    # محاولة تحويل السعر إلى رقم عشري
    try:
        price = float(price_str)
    except ValueError:
        return None, None, None

    # تحديد العملة
    currency = None
    if match.group(1):
        currency = match.group(1).strip()
    elif match.group(3):
        currency = match.group(3).strip()
    elif match.group(4) and match.group(4).lower() in ['k', 'k']:
        # إذا كان هناك K أو k، فهذا يعني آلاف، ونضرب السعر في 1000
        price *= 1000
        # لا يمكن تحديد العملة من K/k فقط، نتركها None أو نحددها بناءً على سياق لاحق
        currency = None 
    
    # إذا لم يتم تحديد العملة، يمكننا محاولة التخمين بناءً على سياق الرسالة أو تركها فارغة
    # لغرض هذا المشروع، سنتركها None إذا لم يتم ذكرها صراحةً
    
    return price, currency, match.span()

# دالة لاستخلاص اسم المنتج
def extract_product_name(text, price_span):
    """
    يستخلص اسم المنتج من النص، مع محاولة استبعاد جزء السعر.
    """
    # إذا تم استخلاص السعر، نركز على الجزء الذي يسبقه
    if price_span:
        text_before_price = text[:price_span[0]].strip()
    else:
        text_before_price = text.strip()

    # منطق بسيط: استخلاص الكلمات الرئيسية قبل السعر
    # يمكن تحسين هذا باستخدام AraBERT لـ NER في المستقبل
    
    # إزالة الكلمات الدالة على السعر أو العرض
    stop_words = ['عرض', 'سعر', 'صفقة', 'خصم', 'الآن', 'فقط', 'جديد', 'للبيع', 'بـ', 'بسعر']
    
    # تقسيم النص إلى كلمات
    words = text_before_price.split()
    
    # تصفية الكلمات
    filtered_words = [word for word in words if word.lower() not in stop_words and len(word) > 1]
    
    # نأخذ آخر 3-5 كلمات كاسم للمنتج (افتراضياً)
    product_name = " ".join(filtered_words[-5:]).strip()
    
    # إذا كان اسم المنتج فارغاً، نستخدم النص الأصلي (أو جزء منه)
    if not product_name:
        return text_before_price[:50].strip()
        
    return product_name

# الدالة الرئيسية للاستخلاص
def extract_price_data(text):
    """
    الدالة الرئيسية لاستخلاص اسم المنتج والسعر والعملة من رسالة تليجرام.
    """
    price, currency, price_span = extract_price_and_currency(text)
    
    if price is None:
        return None, None, None
        
    product_name = extract_product_name(text, price_span)
    
    # تنظيف اسم المنتج من أي رموز أو فواصل غير ضرورية
    product_name = re.sub(r'[^\w\s]', '', product_name).strip()
    
    # تعيين عملة افتراضية إذا لم يتم تحديدها
    if currency is None:
        currency = 'SAR' # افتراضياً الريال السعودي، يمكن تعديله في config.py

    return product_name, price, currency

# مثال للاختبار
if __name__ == '__main__':
    test_messages = [
        "عرض خاص على iPhone 15 Pro Max بسعر 4,500 ريال سعودي اليوم فقط!",
        "سهم ABC ارتفع ليغلق عند 120.50$",
        "BTC الآن بـ 65000 دولار أمريكي",
        "لابتوب Dell جديد بـ 3500 جنيه مصري",
        "تخفيض كبير على ساعة ذكية، السعر النهائي 1.2k",
        "المنتج: هاتف سامسونج S24، السعر: 3,200 د.إ",
        "عرض نهاية الأسبوع: سماعات بلوتوث بـ 99 ريال",
        "السعر الجديد هو ٥٠٠٠ ريال",
        "سعر المنتج هو 1500" # لا يوجد عملة
    ]
    
    print("--- اختبار منطق الاستخلاص ---")
    for msg in test_messages:
        product, price, currency = extract_price_data(msg)
        print(f"الرسالة: {msg}")
        print(f"  المنتج: {product}")
        print(f"  السعر: {price}")
        print(f"  العملة: {currency}")
        print("-" * 20)
