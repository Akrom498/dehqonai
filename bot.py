import asyncio
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import Message
from google import genai
from google.genai import types as genai_types
import requests

TOKEN = "8626509225:AAG8LAYBMuIX3bUCM87BOxaXjT6CknkB_e8"
GEMINI_API_KEY = "AQ.Ab8RN6L-xN1naGR6jTzynhhFzJCqUI86QD2KCThOrh4aJA7MuA"

bot = Bot(token=TOKEN)
dp = Dispatcher()

client = genai.Client(api_key=GEMINI_API_KEY)

AGRONOM_SYSTEM_PROMPT = """
Sen — "DehqonAI" loyihasining bosh sun'iy intellekt agronomisan. Sening vazifang O'zbekistonda (xususan Romitan, Buxoro va Qashqadaryo sharoitida) dehqonlar yuborgan qishloq xo'jaligi ekinlari (paxta, anor, pomidor va boshqalar) bargi yoki mevasining suratini tahlil qilish va ularga aniq, tushunarli, tezkor yechim berish.

Javobni quyidagi strukturada o'zbek tilida ber:
1. 🔬 Aniq tashxis: Ekin va kasallik nomi.
2. 💊 Davolash uchun dori: Tavsiya etiladigan samarali dori nomi.
3. ⚖️ Aniq doza: 1 sotix yoki 1 gektar uchun miqdori.
4. 🕒 Qo'llash tartibi: Qanday va qachon sepish kerakligi.
5. 🌤 Sug'orish eslatmasi: Qisqa ob-havo/sug'orish tavsiyasi.
"""

@dp.message(Command("start"))
async def start_handler(message: Message):
    await message.answer(
        "Assalomu alaykum, hurmatli dehqon! 🌱\n\n"
        "Men **DehqonAI** botiman. Ekiningiz bargi yoki mevasida kasallik alomatlarini sezsangiz, "
        "menga uning **rasmini yuboring**. Men kasallikni aniqlab, qanday dori sepish va dozasini aytib beraman!"
    )

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

        # Model nomi gemini-3.5-flash ga o'zgartirildi
        response = client.models.generate_content(
            model='gemini-3.5-flash',
            contents=[
                genai_types.Part.from_bytes(
                    data=img_bytes,
                    mime_type='image/jpeg',
                ),
                AGRONOM_SYSTEM_PROMPT + "\n\nBu qaysi kasallik? Menga to'liq agronomik maslahat ber."
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

async def main():
    logging.basicConfig(level=logging.INFO)
    print("Bot Gemini orqali ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())