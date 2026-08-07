import asyncio
import logging
import os
from threading import Thread
from flask import Flask
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import google.generativeai as genai
import requests

# Flask server sozlamasi (Render uchun)
app = Flask(__name__)
@app.route('/')
def home():
    return "DehqonAI bot mukammal ishlayapti! 🌿"

def run_web():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

# --- TOKEN VA KALITLAR ---
TOKEN = "8626509225:AAENEY4NLdtayeDyuWBLtvq9_v6Sto9DXeI"
GEMINI_API_KEY = "AQ.Ab8RN6IMetjUzcR-5FfZiaaz1F1PSiBkrjwdKMBHZ4eHAqPYxQ"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Gemini AI sozlamasi
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

AGRONOM_SYSTEM_PROMPT = """
Sen - "DehqonAI" loyihasining bosh sun'iy intellekt agronomisan va O'zbekistonning barcha hududlari iqlimini yaxshi tushunasan. 
Fermer rasm yuborsa — u qanday meva, sabzavot yoki ekanligini, qanday kasalligi borligini aniqlaysan.
Javobni o'zbek tilida quyidagi strukturada ber:
1. 🍎 Meva/Ekin nomi va turi
2. 🔬 Aniq tashxis (kasallik bo'lsa)
3. 💊 Tavsiya etiladigan dori va 10 litr suvga miqdori
4. 🕒 Qo'llash va parvarish qilish tartibi
"""

# O'zbekiston hududlari uchun ob-havoni Open-Meteo orqali olish (API kalit talab qilinmaydi va bepul)
REGION_COORDS = {
    "tashkent": {"name": "Toshkent", "lat": 41.2995, "lon": 69.2401},
    "samarkand": {"name": "Samarqand", "lat": 39.6542, "lon": 66.9597},
    "bukhara": {"name": "Buxoro", "lat": 39.7747, "lon": 64.4286},
    "fergana": {"name": "Farg'ona", "lat": 40.3842, "lon": 71.7843},
    "andijan": {"name": "Andijon", "lat": 40.7821, "lon": 72.3442},
    "namangan": {"name": "Namangan", "lat": 40.9983, "lon": 71.6726},
    "qashqadaryo": {"name": "Qashqadaryo (Qarshi)", "lat": 38.8611, "lon": 65.7874},
    "surxondaryo": {"name": "Surxondaryo (Termiz)", "lat": 37.2242, "lon": 67.2783},
    "navoi": {"name": "Navoiy", "lat": 40.0844, "lon": 65.3792},
    "jizzakh": {"name": "Jizzax", "lat": 40.1158, "lon": 67.8422},
    "sirdaryo": {"name": "Sirdaryo (Guliston)", "lat": 40.4897, "lon": 68.7842},
    "khorezm": {"name": "Xorazm (Urganch)", "lat": 41.55, "lon": 60.6333},
    "karakalpakstan": {"name": "Qoraqalpog'iston (Nukus)", "lat": 42.4647, "lon": 59.6038}
}

# Hududlarni tanlash uchun Inline tugmalar
def get_regions_keyboard():
    keyboard = []
    row = []
    for key, value in REGION_COORDS.items():
        row.append(InlineKeyboardButton(text=value["name"], callback_data=f"weather_{key}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# /start buyrug'i
@dp.message(Command("start"))
async def start_handler(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌤 O'zbekiston bo'yicha ob-havo", callback_data="menu_weather")]
    ])
    await message.answer(
        "Assalomu alaykum! **DehqonAI** botiga xush kelibsiz. 🌿\n\n"
        "• Menga istalgan **meva yoki ekin rasmini** yuboring — uni tanib, kasalligini va dorisini aytaman.\n"
        "• Yoki pastdagi tugma orqali O'zbekistonning istalgan hududi ob-havosini bilib oling!",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

# Ob-havo menyusini ochish
@dp.callback_query(F.data == "menu_weather")
async def weather_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "📍 Hududni tanlang:",
        reply_markup=get_regions_keyboard()
    )
    await callback.answer()

# Tanlangan hudud ob-havosini chiqarish
@dp.callback_query(F.data.startswith("weather_"))
async def show_weather(callback: CallbackQuery):
    region_key = callback.data.split("_")[1]
    data = REGION_COORDS[region_key]
    
    # Open-Meteo bepul ob-havo API so'rovi
    url = f"https://api.open-meteo.com/v1/forecast?latitude={data['lat']}&longitude={data['lon']}&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m"
    try:
        res = requests.get(url).json()
        current = res["current"]
        temp = current["temperature_2m"]
        humidity = current["relative_humidity_2m"]
        wind = current["wind_speed_10m"]
        
        text = (
            f"📍 **Hudud:** {data['name']}\n"
            f"🌡 **Harorat:** {temp}°C\n"
            f"💧 **Namlik:** {humidity}%\n"
            f"💨 **Shamol tezligi:** {wind} m/s\n\n"
            f"Dehqonchilik uchun ob-havo ma'lumoti muvaffaqiyatli aniqlandi! 🌾"
        )
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Boshqa hududni tanlash", callback_data="menu_weather")]
        ])
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    except Exception as e:
        await callback.answer("Ob-havoni olishda xatolik yuz berdi!", show_alert=True)
    
    await callback.answer()

# Rasm yuborganda meva/ekinni va kasallikni aniqlash (Gemini AI)
@dp.message(F.photo)
async def handle_photo(message: Message):
    processing_msg = await message.answer("📸 Rasm tahlil qilinmoqda, iltimos kuting...")
    file = await bot.get_file(message.photo[-1].file_id)
    img_data = requests.get(f"https://api.telegram.org/file/bot{TOKEN}/{file.file_path}").content
    
    try:
        response = model.generate_content([
            {'mime_type': 'image/jpeg', 'data': img_data},
            AGRONOM_SYSTEM_PROMPT + "\n\nBu rasmda qanday meva yoki ekin bor? Uning holatini to'liq tahlil qilib bering."
        ])
        await bot.edit_message_text(text=response.text, chat_id=message.chat.id, message_id=processing_msg.message_id)
    except Exception as e:
        await bot.edit_message_text(text=f"❌ Tahlil qilishda xatolik yuz berdi: {e}", chat_id=message.chat.id, message_id=processing_msg.message_id)

# Oddiy matnli xabarlar uchun (dori dozasini hisoblash)
@dp.message(F.text & ~F.text.startswith("/"))
async def calculate_dose(message: Message):
    processing_msg = await message.answer("⏳ Hisoblanmoqda...")
    try:
        response = model.generate_content(f"{AGRONOM_SYSTEM_PROMPT}\n\nFermerning savoli: {message.text}. 10 litr suvga dozasini va ishlatish tartibini aniq yozib bering.")
        await bot.edit_message_text(text=response.text, chat_id=message.chat.id, message_id=processing_msg.message_id)
    except Exception as e:
        await bot.edit_message_text(text=f"❌ Xatolik: {e}", chat_id=message.chat.id, message_id=processing_msg.message_id)

async def main():
    Thread(target=run_web, daemon=True).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())