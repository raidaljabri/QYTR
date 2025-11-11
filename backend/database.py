import os
from motor.motor_asyncio import AsyncIOMotorClient

# استدعاء متغيرات البيئة
MONGO_DETAILS = os.environ.get("MONGO_URL")  # متغير البيئة على Render
DB_NAME = os.environ.get("DB_NAME", "QYTR")  # قيمة افتراضية

# إنشاء العميل
client = AsyncIOMotorClient(MONGO_DETAILS)

# اختيار قاعدة البيانات
database = client[DB_NAME]

# اختيار الكوليكشن
quotes_collection = database.quotes
