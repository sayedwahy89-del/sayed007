# database.py
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from config import DATABASE_URL

# تعريف القاعدة الأساسية
Base = declarative_base()

# تعريف نموذج جدول الأسعار
class PriceEntry(Base):
    __tablename__ = 'price_entries'

    id = Column(Integer, primary_key=True)
    product_name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    currency = Column(String, default='USD') # يمكن تعديلها حسب الحاجة
    post_date = Column(DateTime, default=datetime.utcnow)
    channel_name = Column(String, nullable=False)
    channel_id = Column(Integer, nullable=False)
    message_id = Column(Integer, nullable=False)
    raw_text = Column(String) # النص الأصلي للرسالة

    def __repr__(self):
        return f"<PriceEntry(product='{self.product_name}', price='{self.price} {self.currency}', channel='{self.channel_name}')>"

# إعداد الاتصال بقاعدة البيانات
engine = create_engine(DATABASE_URL)

# إنشاء الجداول في قاعدة البيانات (إذا لم تكن موجودة)
def init_db():
    Base.metadata.create_all(engine)

# إعداد مُنشئ الجلسات
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# دالة مساعدة للحصول على جلسة قاعدة البيانات
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized and tables created.")
