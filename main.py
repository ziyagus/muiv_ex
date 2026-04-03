import asyncio
import json
import random
from datetime import datetime
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

# система очков
POINTS_CORRECT = 10
POINTS_WRONG = -5

# создаем объекты бота и диспетчера
bot = Bot(token=TOKEN_BOT)
dp = Dispatcher()

# хранилище для вопросов и пользователей
questions_pdd = []
questions_auto = []
questions_car = []
users_data = {}

# словарь для хранения текущих игр пользователей
user_games = {}

# функция загрузки данных пользователей
def load_users():
    global users_data
    try:
        with open(USERS_DB, 'r', encoding='utf-8') as f:
            users_data = json.load(f)
        print(f"✅ Загружено {len(users_data)} пользователей")
    except FileNotFoundError:
        # если файла нет - создаем пустой словарь
        users_data = {}
        print("⚠️ Файл users.json не найден, создан новый")
    except:
        users_data = {}
        print("❌ Ошибка загрузки users.json")

# функция сохранения данных пользователей
def save_users():
    try:
        with open(USERS_DB, 'w', encoding='utf-8') as f:
            json.dump(users_data, f, ensure_ascii=False, indent=2)
    except:
        print("❌ Ошибка сохранения users.json")

# функция получения или создания профиля пользователя
def get_user_profile(user_id, username="Unknown"):
    user_id_str = str(user_id)
    
    # если пользователя нет - создаем новый профиль
    if user_id_str not in users_data:
        users_data[user_id_str] = {
            "username": username,
            "total_score": 0,
            "games_played": 0,
            "correct_answers": 0,
            "wrong_answers": 0,
            "exams_passed": 0,
            "pdd_games": 0,
            "auto_games": 0,
            "car_quiz_games": 0,
            "random_games": 0,
            "exam_games": 0,
            "last_played": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        save_users()
    
    return users_data[user_id_str]

# функция обновления очков пользователя
def update_user_score(user_id, points, is_correct, mode):
    user_id_str = str(user_id)
    profile = users_data[user_id_str]
    
    # обновляем общие очки
    profile['total_score'] += points
    
    # обновляем статистику ответов
    if is_correct:
        profile['correct_answers'] += 1
    else:
        profile['wrong_answers'] += 1
    
    # обновляем счетчик игр по режиму
    if mode == "pdd":
        profile['pdd_games'] = profile.get('pdd_games', 0) + 1
    elif mode == "auto":
        profile['auto_games'] = profile.get('auto_games', 0) + 1
    
    # обновляем дату последней игры
    profile['last_played'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # сохраняем изменения
    save_users()

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
    buttons = []
    for i, answer in enumerate(question['answers']):
        button = InlineKeyboardButton(
            text=answer,
            callback_data=f"answer_{question_index}_{i}"
        )
        buttons.append([button])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard

# функция отправки вопроса пользователю
async def send_question(chat_id, mode):
    if mode == "pdd":
        questions_list = questions_pdd
        emoji = "🚦"
    elif mode == "auto":
        questions_list = questions_auto
        emoji = "🚗"
    else:
        return
    
    question = random.choice(questions_list)
    question_index = questions_list.index(question)
    
    user_games[chat_id] = {
        "mode": mode,
        "question": question,
        "question_index": question_index,
        "questions_list": questions_list
    }
    
    question_text = f"{emoji} <b>Вопрос:</b>\n\n{question['question']}"
    
    await bot.send_message(
        chat_id,
        question_text,
        parse_mode="HTML",
        reply_markup=create_answer_keyboard(question, question_index)
    )

# функция проверки ответа
async def check_answer(callback: types.CallbackQuery, question_index, answer_index):
    chat_id = callback.message.chat.id
    user_id = callback.from_user.id
    username = callback.from_user.username or callback.from_user.first_name
    
    # получаем или создаем профиль пользователя
    get_user_profile(user_id, username)
    
    if chat_id not in user_games:
        await callback.message.answer("❌ Нет активной игры. Начни новую через /start")
        return
    
    game = user_games[chat_id]
    question = game['question']
    
    # проверяем правильность ответа
    is_correct = (answer_index == question['correct'])
    
    if is_correct:
        points = POINTS_CORRECT
        emoji = "✅"
        result_text = f"{emoji} <b>Правильно!</b>\n\n💰 +{points} очков"
    else:
        points = POINTS_WRONG
        emoji = "❌"
        correct_answer = question['answers'][question['correct']]
        result_text = f"{emoji} <b>Неправильно!</b>\n\n"
        result_text += f"Правильный ответ: {correct_answer}\n\n"
        result_text += f"💸 {points} очков"
    
    # обновляем очки пользователя
    update_user_score(user_id, points, is_correct, game['mode'])
    
    # получаем обновленный профиль
    profile = users_data[str(user_id)]
    result_text += f"\n\n📊 Всего очков: {profile['total_score']}"
    
    await callback.message.answer(result_text, parse_mode="HTML")
    
    del user_games[chat_id]
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➡️ Следующий вопрос", callback_data=f"mode_{game['mode']}")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ])
    
    await callback.message.answer("Что дальше?", reply_markup=keyboard)

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
    # создаем профиль если его нет
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    get_user_profile(user_id, username)
    
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
    
    if data == "main_menu":
        welcome_text = "🚗 <b>AutoQuiz</b>\n\nВыбери режим игры:"
        await callback.message.answer(welcome_text, parse_mode="HTML", reply_markup=get_main_menu())
    
    elif data == "mode_pdd":
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
    
    elif data.startswith("answer_"):
        parts = data.split("_")
        question_index = int(parts[1])
        answer_index = int(parts[2])
        await check_answer(callback, question_index, answer_index)
    
    await callback.answer()

# главная функция запуска бота
async def main():
    load_questions()
    load_users()
    print("🤖 Бот запущен!")
    await dp.start_polling(bot)

# запуск программы
if __name__ == "__main__":
    asyncio.run(main())
