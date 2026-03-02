import asyncio
import json
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# токен бота
TOKEN_BOT = "token"

# пути к нашим файлам с данными
QUESTIONS_PDD = "data/questions_pdd.json"
QUESTIONS_AUTO = "data/questions_auto.json"
CAR_QUIZ = "data/car_quiz.json"
USERS_DB = "data/users.json"

# создаем объекты бота и диспетчера
bot = Bot(token=TOKEN_BOT)
dp = Dispatcher()

# хранилище для вопросов
questions_pdd = []
questions_auto = []
questions_car = []

# функция загрузки вопросов из json
def load_questions():
    global questions_pdd, questions_auto, questions_car
    
    # загружаем вопросы по пдд + логируем
    try:
        with open(QUESTIONS_PDD, 'r', encoding='utf-8') as f:
            questions_pdd = json.load(f)
        print(f"✅ Загружено {len(questions_pdd)} вопросов ПДД")
    except:
        print("❌ Ошибка загрузки questions_pdd.json")
    
    # загружаем автофакты + логируем
    try:
        with open(QUESTIONS_AUTO, 'r', encoding='utf-8') as f:
            questions_auto = json.load(f)
        print(f"✅ Загружено {len(questions_auto)} автофактов")
    except:
        print("❌ Ошибка загрузки questions_auto.json")
    
    # загружаем викторину с машинами и тоже логируем
    try:
        with open(CAR_QUIZ, 'r', encoding='utf-8') as f:
            questions_car = json.load(f)
        print(f"✅ Загружено {len(questions_car)} вопросов с фото машин")
    except:
        print("❌ Ошибка загрузки car_quiz.json")

# функция создания главного меню
def get_main_menu():
    # создаем клавиатуру главного меню с кнопками
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚦 Тест ПДД", callback_data="mode_pdd")],
        [InlineKeyboardButton(text="🚗 Автофакты", callback_data="mode_auto")],
        [InlineKeyboardButton(text="🚘 Угадай машину по фото", callback_data="mode_car_quiz")],
        [InlineKeyboardButton(text="🎲 Случайная викторина", callback_data="mode_random")],
        [InlineKeyboardButton(text="🏁 Экзамен", callback_data="mode_exam")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")],
        [InlineKeyboardButton(text="🏆 Рейтинг", callback_data="rating")],
    ])
    return keyboard

# обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    welcome_text = (
        "🚗 <b>Привет! Это AutoQuiz!</b>\n\n"
        "🏁 Викторина про ПДД и автомобили,\n"
        "где ты можешь прокачать свои знания или же просто проверить их!\n\n"
        "Выбери режим игры:"
    )
    await message.answer(welcome_text, parse_mode="HTML", reply_markup=get_main_menu())

# обработчик нажатий на кнопки
@dp.callback_query()
async def handle_callback(callback: types.CallbackQuery):
    data = callback.data
    
    # показываем сколько вопросов доступно
    if data == "mode_pdd":
        await callback.message.answer(f"🚦 Режим 'Тест ПДД'\n📝 Доступно вопросов: {len(questions_pdd)}")
    elif data == "mode_auto":
        await callback.message.answer(f"🚗 Режим 'Автофакты'\n📝 Доступно вопросов: {len(questions_auto)}")
    elif data == "mode_car_quiz":
        await callback.message.answer(f"🚘 Режим 'Угадай машину'\n📝 Доступно вопросов: {len(questions_car)}")
    elif data == "mode_random":
        total = len(questions_pdd) + len(questions_auto)
        await callback.message.answer(f"🎲 Случайная викторина\n📝 Доступно вопросов: {total}")
    elif data == "mode_exam":
        await callback.message.answer("🏁 Режим 'Экзамен' (в разработке)")
    elif data == "profile":
        await callback.message.answer("👤 Твой профиль (в разработке)")
    elif data == "rating":
        await callback.message.answer("🏆 Рейтинг игроков (в разработке)")
    
    await callback.answer()

# главная функция запуска бота
async def main():
    # загружаем вопросы перед запуском
    load_questions()
    
    # запуск бота
    print("Бот запущен!")
    await dp.start_polling(bot)

# запуск программы
if __name__ == "__main__":
    asyncio.run(main())



