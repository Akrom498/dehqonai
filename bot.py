import asyncio
import logging
import os
from threading import Thread
from flask import Flask
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message
import google.generativeai as genai
import requests

# Flask server sozlamasi
app = Flask(__name__)
@app.route('/')
def home():
    return "DehqonAI bot ishlayapti! 🌿"

def run_web():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

# --- MA'LUMOTLARINGIZNI SHU YERGA YOZING ---
TOKEN = "8626509225:AAG8LAYBMuIX3bUCM87BOxaXjT6CknkB_e8"
GEMINI_API_KEY = "AQ.Ab8RN6IMetjUzcR-5FfZiaaz1F1PSiBkrjwdKMBHZ4eHAqPYxQ"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Eski barqaror kutubxonani sozlash
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

AGRONOM_SYSTEM_PROMPT = """
Sen - "DehqonAI" loyihasining bosh sun'iy intellekt agronomisan. 
Siz O'zbekiston dehqonlariga yordam berasiz. Har qanday ekin (pomidor, bodring, bulg'or qalampiri, va boshqalar) bo'yicha maslahat berasiz.

Javobni quyidagi strukturada o'zbek tilida ber:
1. 🔬 Aniq tashxis: Ekin va kasallik nomi.
2. 💊 Davolash uchun dori: Tavsiya etiladigan samarali dori nomi.
3. ⚖️ Aniq doza: 10 litr suvga, 1 sotix yoki 1 gektar uchun miqdori.
4. 🕒 Qo'llash tartibi: Qanday va qachon sepish kerakligi.
5. ⛅ Sug'orish eslatmasi: Qisqa ob-havo/sug'orish tavsiyasi.
"""

@dp.message(Command("start"))
async def start_handler(message: Message):
    await message.answer("Assalomu alaykum! DehqonAI ishga tushdi. Ekin rasmini yuboring yoki dori dozasini so'rang.")

# 1. Rasm tahlili
@dp.message(F.photo)
async def handle_photo(message: Message):
    processing_msg = await message.answer("📸 Tahlil qilinmoqda...")
    file = await bot.get_file(message.photo[-1].file_id)
    img_data = requests.get(f"https://api.telegram.org/file/bot{TOKEN}/{file.file_path}").content
    
    try:
        response = model.generate_content([
            {'mime_type': 'image/jpeg', 'data': img_data},
            AGRONOM_SYSTEM_PROMPT + "\n\nBu rasmda qanday ekin va qanday kasallik bor? To'liq agronomik maslahat bering."
        ])
        await bot.edit_message_text(text=response.text, chat_id=message.chat.id, message_id=processing_msg.message_id)
    except Exception as e:
        await bot.edit_message_text(text=f"❌ Xatolik: {e}", chat_id=message.chat.id, message_id=processing_msg.message_id)

# 2. Dori hisoblagich
@dp.message(F.text & ~F.text.startswith("/"))
async def calculate_dose(message: Message):
    processing_msg = await message.answer("⏳ Hisoblanmoqda...")
    try:
        response = model.generate_content(f"{AGRONOM_SYSTEM_PROMPT}\n\nFermer savoli: {message.text}. 10 litr suvga dozasini aniq hisoblab bering.")
        await bot.edit_message_text(text=response.text, chat_id=message.chat.id, message_id=processing_msg.message_id)
    except Exception as e:
        await bot.edit_message_text(text=f"❌ Xatolik: {e}", chat_id=message.chat.id, message_id=processing_msg.message_id)

async def main():
    Thread(target=run_web, daemon=True).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())