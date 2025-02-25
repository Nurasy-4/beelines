import logging
import asyncio
import re
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

API_TOKEN = '7823391741:AAHJ5C-6FfQUYlmWX-cosVzI7-dEBwfk_Ag'
ADMIN_ID = 8034258045

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

user_gb_selection = {}
payment_approved = {}
gb_confirmed = {}

start_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔢 ГБ есептеу")],
        [KeyboardButton(text="📲 Нөміріңізді жіберу", request_contact=True)]
    ],
    resize_keyboard=True
)

gb_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🟩 1 ГБ"), KeyboardButton(text="🟩 2 ГБ")],
        [KeyboardButton(text="🟩 3 ГБ"), KeyboardButton(text="🟩 4 ГБ")],
        [KeyboardButton(text="🟩 5 ГБ"), KeyboardButton(text="🟩 6 ГБ")],
        [KeyboardButton(text="🟩 7 ГБ"), KeyboardButton(text="🟩 8 ГБ")],
        [KeyboardButton(text="🟩 9 ГБ"), KeyboardButton(text="🟩 10 ГБ")],
    ],
    resize_keyboard=True
)

payment_done_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="✅ Оплата жасадым")]
    ],
    resize_keyboard=True
)

payment_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📲 Нөміріңізді жіберу", request_contact=True)],
        [KeyboardButton(text="✍ Қолмен нөмір енгізу")]
    ],
    resize_keyboard=True
)

restart_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔄 Қайта бастау")]
    ],
    resize_keyboard=True
)

def get_gb_confirm_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="✅ ГБ түсті")]],
        resize_keyboard=True
    )

@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.reply("Сәлем! Қанша ГБ керектігін таңдаңыз!", reply_markup=gb_keyboard)

@dp.message(F.text.startswith("🟩"))
async def calculate_price(message: types.Message):
    try:
        gb_amount = int(message.text.split(" ")[1].replace("ГБ", ""))
        price = gb_amount * 110
        user_gb_selection[message.from_user.id] = gb_amount
        await message.reply(
            f"{gb_amount} ГБ = {price} ₸.\n\n✅ Төлеу реквизиттері: 8 705 213 51 07\nАты: Алеухан Нұрасыл\n\nЕгер төлем жасасаңыз, 'Оплата жасадым' батырмасын басыңыз.",
            reply_markup=payment_done_keyboard
        )
    except ValueError:
        await message.reply("Қате! Дұрыс ГБ мөлшерін таңдаңыз.")

@dp.message(F.text == "✅ Оплата жасадым")
async def payment_confirmation(message: types.Message):
    user_id = message.from_user.id
    await bot.send_message(
        ADMIN_ID,
        f"📌 Қолданушы @{message.from_user.username} ({message.from_user.full_name}) төлем жасады. Растайсыз ба?",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="✅ Растау", callback_data=f"approve_{user_id}")]]
        )
    )
    await message.reply("✅ Төлеміңіз тексерілуде.")

@dp.callback_query(F.data.startswith("approve_"))
async def approve_payment(callback: types.CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    payment_approved[user_id] = True
    await bot.send_message(user_id, "✅ Төлем расталды! Нөміріңізді бөлісе аласыз.", reply_markup=payment_keyboard)
    await callback.answer("Төлем расталды!")

@dp.message(F.text == "✍ Қолмен нөмір енгізу")
async def request_manual_phone(message: types.Message):
    await message.reply("📞 Нөміріңізді енгізіңіз (мысалы: +77051234567 немесе 87051234567):")

@dp.message(F.contact)
async def handle_contact(message: types.Message):
    user_id = message.from_user.id
    if not payment_approved.get(user_id, False):
        await message.reply("⚠️ Төлем әлі расталған жоқ!")
        return
    contact = message.contact.phone_number
    await process_phone_number(message, contact)

@dp.message(F.text.regexp(r"^(\+7|8)\d{10}$"))  # +7 + 10 цифр или 8 + 10 цифр

async def handle_manual_phone(message: types.Message):
    user_id = message.from_user.id
    if not payment_approved.get(user_id, False):
        await message.reply("⚠️ Төлем әлі расталған жоқ!")
        return
    await process_phone_number(message, message.text)

async def process_phone_number(message: types.Message, phone_number: str):
    user_id = message.from_user.id
    gb_amount = user_gb_selection.get(user_id, "белгісіз")
    gb_confirmed[user_id] = False
    await message.reply(
        f"✅ Нөміріңіз қабылданды: {phone_number}\nЖақын арада ГБ түсетін болады!\nТҮСКЕННЕН КЕЙІН  👉ГБ ТҮСТІ👈 БАТЫРМАСЫН БАСЫҢЫЗ", 
        reply_markup=get_gb_confirm_keyboard()
    )
    await bot.send_message(
        ADMIN_ID,
        f"🆕 Жаңа тапсырыс!\n👤 Қолданушы: @{message.from_user.username}\n🔑 Telegram ID: {user_id}\n📞 Нөмір: {phone_number}\n📦 Трафик: {gb_amount} ГБ\n🟢 Статус: Төлем расталды"
    )

@dp.message(F.text == "✅ ГБ түсті")
async def confirm_gb_sent(message: types.Message):
    user_id = message.from_user.id
    if user_id in gb_confirmed and not gb_confirmed[user_id]:
        gb_confirmed[user_id] = True
        await message.reply("✅ ГБ сәтті жіберілді!", reply_markup=restart_keyboard)
        await bot.send_message(ADMIN_ID, f"✅ ГБ қолданушыға жіберілді: @{message.from_user.username}")

@dp.message(F.text == "🔄 Қайта бастау")
async def restart_order(message: types.Message):
    await message.reply("🔄 Жаңа тапсырыс жасау үшін ГБ мөлшерін таңдаңыз!", reply_markup=gb_keyboard)

@dp.message()
async def handle_invalid_input(message: types.Message):
    if message.text:
        await message.reply("❌ Қате! Дұрыс нөмір енгізіңіз (мысалы: +77051234567 немесе 87051234567).")

async def main():
    await dp.start_polling(bot, skip_updates=True)

if __name__ == '__main__':
    asyncio.run(main())