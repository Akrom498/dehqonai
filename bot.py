import asyncio
import logging
import os
from threading import Thread
from flask import Flask
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import Message
from google import genai
from google.genai import types as genai_types
import requests

# --- Render uxlab qolmasligi va port talabini qondirish uchun Flask server ---
app = Flask(__name__)

@app.route('/')
def home():
    return "DehqonAI bot ishlayapti! 🌿"

def run_web():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

# --- Token va API kalitlarni muhit o'zgaruvchilaridan olish ---
TOKEN = os.environ.get("8626509225:AAG8LAYBMuIX3bUCM87BOxaXjT6CknkB_e8")
GEMINI_API_KEY = os.environ.get("AQ.Ab8RN6IMetjUzcR-5FfZiaaz1F1PSiBkrjwdKMBHZ4eHAqPYxQ")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Yangi kutubxona uchun to'g'ri ulanish
client = genai.Client(api_key=GEMINI_API_KEY)

# --- Agrotexnik prompt (Asosiy ekinlarga alohida e'tibor bilan) ---
AGRONOM_SYSTEM_PROMPT = """
Sen - "DehqonAI" loyihasining bosh sun'iy intellekt agronomisan. 
Siz O'zbekiston dehqonlariga yordam berasiz. Asosiy ekinlarimiz pomidor, bodring va bulg'or qalampiri hisoblanadi (ularga alohida chuqur va aniq maslahat berasiz). Lekin boshqa har qanday ekin yoki sabzavot bo'yicha ham dehqonga yordam bering.

Javobni quyidagi strukturada o'zbek tilida ber:
1. 🔬 Aniq tashxis: Ekin va kasallik nomi.
2. 💊 Davolash uchun dori: Tavsiya etiladigan samarali dori nomi.
3. ⚖️ Aniq doza: 10 litr suvga, 1 sotix yoki 1 gektar uchun miqdori (dehqon adashmasligi uchun).
4. 🕒 Qo'llash tartibi: Qanday va qachon sepish kerakligi.
5. ⛅ Sug'orish eslatmasi: Qisqa ob-havo/sug'orish tavsiyasi.
"""

@dp.message(Command("start"))
async def start_handler(message: Message):
    await message.answer(
        "Assalomu alaykum, hurmatli dehqon! 🌿\n\n"
        "Men **DehqonAI** botiman. Har qanday ekin yoki sabzavotingiz bo'yicha yordam beraman "
        "(pomidor, bodring va bulg'or qalampiriga esa eng mukammal tavsiyalarni beraman).\n\n"
        "Ekingiz bargi yoki mevasida kasallik alomatlarini sezsangiz, **rasmini yuboring** yoki "
        "dori dozasini bilish uchun **matn yozib yuboring**!"
    )

# 1. Rasm yuborganda kasallikni aniqlash va dozasini aytish
@dp.message(F.photo)
async def handle_photo(message: Message):
    processing_msg = await message.answer("📸 Rasm qabul qilindi, Gemini AI tahlil qilmoqda...")
    
    photo = message.photo[-1]
    file_info = await bot.get_file(photo.file_id)
    file_path = file_info.file_path
    
    image_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"
    
    try:
        img_response = requests.get(image_url)
        img_bytes = img_response.content

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[
                genai_types.Part.from_bytes(
                    data=img_bytes,
                    mime_type='image/jpeg',
                ),
                AGRONOM_SYSTEM_PROMPT + "\n\nBu rasmda qanday ekin va qanday kasallik bor? Menga to'liq agronomik maslahat va 10 litr suvga dozasini ber."
            ]
        )
        
        ai_answer = response.text

        await bot.edit_message_text(
            text=ai_answer,
            chat_id=message.chat.id,
            message_id=processing_msg.message_id
        )
        
    except Exception as e:
        logging.error(f"Xatolik yuz berdi: {e}")
        await bot.edit_message_text(
            text=f"❌ Tizim xatoligi: {e}",
            chat_id=message.chat.id,
            message_id=processing_msg.message_id
        )

# 2. Dori hisoblagich va matnli savollar uchun
@dp.message(F.text & ~F.text.startswith("/"))
async def calculate_medicine_dose(message: Message):
    user_text = message.text
    processing_msg = await message.answer("⏳ Hisoblanmoqda...")
    
    prompt = (
        f"{AGRONOM_SYSTEM_PROMPT}\n\n"
        f"Fermerning savoli yoki ishlatmoqchi bo'lgan dorisi: '{user_text}'. "
        "Dehqonga tushunarli qilib, 10 litr suvga necha gramm/millilitr solish kerakligini va 1 sotixga sarfini aniq hisoblab ber."
    )
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        await bot.edit_message_text(
            text=response.text,
            chat_id=message.chat.id,
            message_id=processing_msg.message_id
        )
    except Exception as e:
        await bot.edit_message_text(
            text=f"❌ Xatolik yuz berdi: {e}",
            chat_id=message.chat.id,
            message_id=processing_msg.message_id
        )

async def main():
    logging.basicConfig(level=logging.INFO)
    
    # Flask serverini alohida oqimda (thread) ishga tushiramiz
    server_thread = Thread(target=run_web)
    server_thread.daemon = True
    server_thread.start()

    print("Bot va veb-server Gemini orqali ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())