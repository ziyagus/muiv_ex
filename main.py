import asyncio
import json
import random
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# токен бота
TOKEN_BOT = "token"

# пути к файлам
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

# словарь для хранения текущих игр пользователей
user_games = {}

# функция загрузки вопросов из json
def load_questions():
    global questions_pdd, questions_auto, questions_car
    
    try:
        with open(QUESTIONS_PDD, 'r', encoding='utf-8') as f:
            questions_pdd = json.load(f)
        print(f"✅ Загружено {len(questions_pdd)} вопросов ПДД")
    except:
        print("❌ Ошибка загрузки questions_pdd.json")
    
    try:
        with open(QUESTIONS_AUTO, 'r', encoding='utf-8') as f:
            questions_auto = json.load(f)
        print(f"✅ Загружено {len(questions_auto)} автофактов")
    except:
        print("❌ Ошибка загрузки questions_auto.json")
    
    try:
        with open(CAR_QUIZ, 'r', encoding='utf-8') as f:
            questions_car = json.load(f)
        print(f"✅ Загружено {len(questions_car)} вопросов с фото машин")
    except:
        print("❌ Ошибка загрузки car_quiz.json")

# функция создания клавиатуры с вариантами ответов
def create_answer_keyboard(question, question_index):
    # создаем кнопки для каждого варианта ответа
    buttons = []
    for i, answer in enumerate(question['answers']):
        # в callback_data передаем индекс вопроса и индекс ответа
        button = InlineKeyboardButton(
            text=answer,
            callback_data=f"answer_{question_index}_{i}"
        )
        buttons.append([button])  # каждая кнопка на отдельной строке
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard

# функция отправки вопроса пользователю
async def send_question(chat_id, mode):
    # выбираем список вопросов в зависимости от режима
    if mode == "pdd":
        questions_list = questions_pdd
        emoji = "🚦"
    elif mode == "auto":
        questions_list = questions_auto
        emoji = "🚗"
    else:
        return
    
    # выбираем случайный вопрос
    question = random.choice(questions_list)
    question_index = questions_list.index(question)
    
    # сохраняем информацию об игре пользователя
    user_games[chat_id] = {
        "mode": mode,
        "question": question,
        "question_index": question_index
    }
    
    # формируем текст вопроса
    question_text = f"{emoji} <b>Вопрос:</b>\n\n{question['question']}"
    
    # отправляем вопрос с вариантами ответов
    await bot.send_message(
        chat_id,
        question_text,
        parse_mode="HTML",
        reply_markup=create_answer_keyboard(question, question_index)
    )

# функция создания главного меню
def get_main_menu():
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
    chat_id = callback.message.chat.id
    
    # обработка выбора режима
    if data == "mode_pdd":
        await callback.message.answer("🚦 <b>Тест ПДД</b>\n\nСейчас будет вопрос!", parse_mode="HTML")
        await send_question(chat_id, "pdd")
    elif data == "mode_auto":
        await callback.message.answer("🚗 <b>Автофакты</b>\n\nСейчас будет вопрос!", parse_mode="HTML")
        await send_question(chat_id, "auto")
    elif data == "mode_car_quiz":
        await callback.message.answer("🚘 Режим 'Угадай машину' (в разработке)")
    elif data == "mode_random":
        await callback.message.answer("🎲 Случайная викторина (в разработке)")
    elif data == "mode_exam":
        await callback.message.answer("🏁 Режим 'Экзамен' (в разработке)")
    elif data == "profile":
        await callback.message.answer("👤 Твой профиль (в разработке)")
    elif data == "rating":
        await callback.message.answer("🏆 Рейтинг игроков (в разработке)")
    
    # обработка ответов на вопросы
    elif data.startswith("answer_"):
        # пока просто показываем что ответ получен
        await callback.message.answer("Ответ получен!")
    
    await callback.answer()

# главная функция запуска бота
async def main():
    load_questions()
    print("🤖 Бот запущен!")
    await dp.start_polling(bot)

# запуск программы
if __name__ == "__main__":
    asyncio.run(main())

