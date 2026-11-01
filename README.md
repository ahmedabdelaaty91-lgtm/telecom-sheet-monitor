# Telecom Google Sheet to Telegram Monitor

يقوم هذا المشروع بمتابعة شيت جوجل بشكل آلي، وتوليد جدول Pivot Table مطابق لشيت الإكسيل، وإرساله فور حدوث أي تحديث كصورة إلى تيليجرام.

## الملفات المتاحة
- `generate_pivot_image.py`: استخراج وتجميع البيانات وتوليد صورة الجدول باحترافية وتطابق تام.
- `monitor.py`: فحص الشيت كل ساعة تلقائياً (أو حسب الإعدادات) واكتشاف أي تعديل وإرسال الصورة للتيليجرام.
- `config.json`: ملف الإعدادات الخاص برابط الشيت وتيليجرام ومعدل الفحص.
- `run_monitor.bat`: ملف تشغيل مباشر بنقرة واحدة على ويندوز.

## خطوات الإعداد للتيليجرام:
1. أنشئ بوت تيليجرام عبر محادثة [@BotFather](https://t.me/BotFather) واستخرج الـ `Bot Token`.
2. احصل على الـ `Chat ID` الخاص بك عبر إرسال أي رسالة للبوت [@userinfobot](https://t.me/userinfobot).
3. افتح ملف `config.json` وضع التوكن والـ Chat ID:
```json
{
    "sheet_url": "https://docs.google.com/spreadsheets/d/1nv8eAlRiUQAqYy5cL5V_LhQl0Ht6tD3caFKUZoVQrOY/export?format=csv&gid=0",
    "telegram_bot_token": "ضع_توكن_البوت_هنا",
    "telegram_chat_id": "ضع_ال_Chat_ID_هنا",
    "check_interval_seconds": 3600,
    "send_on_start": true
}
```
4. شغّل ملف `run_monitor.bat`.
