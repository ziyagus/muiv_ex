import asyncio
import json
import random
import logging
import os
import shutil
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile

# токен бота
TOKEN_BOT = "token"

QUESTIONS_PDD = "data/questions_pdd.json"
QUESTIONS_AUTO = "data/questions_auto.json"
CAR_QUIZ = "data/car_quiz.json"
USERS_DB = "data/users.json"
USERS_BACKUP = "data/users_backup.json"
LOG_FILE = "log.txt"

POINTS_CORRECT = 10  # очки за правильный ответ
POINTS_WRONG = -5    # штраф за ошибку
EXAM_QUESTIONS_COUNT = 20  # количество вопросов в экзамене

# настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# создаем объекты бота и диспетчера
bot = Bot(token=TOKEN_BOT)
dp = Dispatcher()

questions_pdd = []
questions_auto = []
questions_car = []
users_data = {}

user_games = {}
user_exams = {}

last_button_press = {}

# мотивирующие фразы
positive_phrases = ["Отлично! 🎉", "Супер! 💪", "Молодец! 🌟", "Так держать! 🚀", "Круто! 🔥", "Ты на высоте! ⭐"]
negative_phrases = ["Ничего, в следующий раз получится! 💪", "Не расстраивайся, продолжай! 🎯", "Учимся на ошибках! 📚", "Попробуй еще раз! 🔄", "Так бывает! 🤷‍♂️"]

# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ 

def check_spam(user_id, interval=1):
    """проверяет прошло ли достаточно времени с последнего нажатия"""
    current_time = datetime.now()
    user_id_str = str(user_id)
    
    if user_id_str in last_button_press:
        time_diff = (current_time - last_button_press[user_id_str]).total_seconds()
        if time_diff < interval:
            return False
    
    last_button_press[user_id_str] = current_time
    return True

def load_users():
    """загружает данные пользователей из json"""
    global users_data
    try:
        with open(USERS_DB, 'r', encoding='utf-8') as f:
            users_data = json.load(f)
        logging.info(f"Загружено {len(users_data)} пользователей")
    except FileNotFoundError:
        users_data = {}
        logging.warning("Файл users.json не найден, создан новый")
        save_users()
    except json.JSONDecodeError:
        try:
            with open(USERS_BACKUP, 'r', encoding='utf-8') as f:
                users_data = json.load(f)
            logging.warning("Загружен бэкап users.json")
        except:
            users_data = {}
            logging.error("Ошибка формата users.json, создан новый")
            save_users()
    except Exception as e:
        users_data = {}
        logging.error(f"Ошибка загрузки users.json: {e}")

def save_users():
    """сохраняет данные пользователей в json"""
    try:
        if os.path.exists(USERS_DB):
            shutil.copy2(USERS_DB, USERS_BACKUP)
        
        with open(USERS_DB, 'w', encoding='utf-8') as f:
            json.dump(users_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"Ошибка сохранения users.json: {e}")

def get_user_profile(user_id, username="Unknown"):
    """получает или создает профиль пользователя"""
    user_id_str = str(user_id)
    
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
        logging.info(f"Создан новый пользователь: {username} (ID: {user_id})")
    
    return users_data[user_id_str]

def update_user_score(user_id, points, is_correct, mode):
    """обновляет очки пользователя"""
    user_id_str = str(user_id)
    profile = users_data[user_id_str]
    
    profile['total_score'] += points
    
    if is_correct:
        profile['correct_answers'] += 1
    else:
        profile['wrong_answers'] += 1
    
    if mode == "pdd":
        profile['pdd_games'] = profile.get('pdd_games', 0) + 1
    elif mode == "auto":
        profile['auto_games'] = profile.get('auto_games', 0) + 1
    elif mode == "random":
        profile['random_games'] = profile.get('random_games', 0) + 1
    elif mode == "car_quiz":
        profile['car_quiz_games'] = profile.get('car_quiz_games', 0) + 1
    
    profile['last_played'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    save_users()
    
    result = "правильно" if is_correct else "неправильно"
    logging.info(f"Пользователь {profile['username']} ответил {result} в режиме {mode}. Очки: {points}")

def get_profile_text(user_id):
    """формирует текст профиля пользователя"""
    user_id_str = str(user_id)
    
    if user_id_str not in users_data:
        return "❌ Профиль не найден. Начни игру через /start"
    
    profile = users_data[user_id_str]
    
    username = profile.get('username', 'Unknown')
    total_score = profile.get('total_score', 0)
    correct = profile.get('correct_answers', 0)
    wrong = profile.get('wrong_answers', 0)
    total_answers = correct + wrong
    exams_passed = profile.get('exams_passed', 0)
    
    if total_answers > 0:
        accuracy = (correct / total_answers) * 100
    else:
        accuracy = 0
    
    profile_text = (
        f"╔═══════════════════╗\n"
        f"👤 <b>{username}</b>\n"
        f"╚═══════════════════╝\n\n"
        f"💰 <b>Очки:</b> {total_score}\n"
        f"✅ <b>Правильно:</b> {correct}\n"
        f"❌ <b>Неправильно:</b> {wrong}\n"
        f"📊 <b>Точность:</b> {accuracy:.1f}%\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🚦 ПДД: {profile.get('pdd_games', 0)}\n"
        f"🚗 Автофакты: {profile.get('auto_games', 0)}\n"
        f"🚘 Угадай авто: {profile.get('car_quiz_games', 0)}\n"
        f"🎲 Случайные: {profile.get('random_games', 0)}\n"
        f"🏁 Экзаменов сдано: {exams_passed}\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🕐 Последняя игра:\n{profile.get('last_played', 'Никогда')}"
    )
    
    return profile_text

def reset_user_progress(user_id):
    """сбрасывает прогресс пользователя"""
    user_id_str = str(user_id)
    
    if user_id_str in users_data:
        username = users_data[user_id_str].get('username', 'Unknown')
        
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
        logging.info(f"Пользователь {username} (ID: {user_id}) сбросил прогресс")
        return True
    
    return False

def get_rating_text():
    """формирует текст рейтинга игроков"""
    sorted_users = sorted(
        users_data.items(),
        key=lambda x: x[1].get('total_score', 0),
        reverse=True
    )
    
    top_users = sorted_users[:10]
    
    if not top_users:
        return "🏆 <b>Рейтинг пуст</b>\n\nСтань первым игроком! 🚀"
    
    rating_text = (
        "╔═══════════════════╗\n"
        "🏆 <b>ТОП ИГРОКОВ</b>\n"
        "╚═══════════════════╝\n\n"
    )
    
    medals = ["🥇", "🥈", "🥉"]
    
    for i, (user_id, profile) in enumerate(top_users, 1):
        if i <= 3:
            position_emoji = medals[i - 1]
        else:
            position_emoji = f"{i}."
        
        username = profile.get('username', 'Unknown')
        score = profile.get('total_score', 0)
        
        rating_text += f"{position_emoji} <b>{username}</b>\n    💰 {score} очков\n\n"
    
    return rating_text

def get_bot_stats():
    """возвращает общую статистику бота"""
    total_users = len(users_data)
    total_questions = len(questions_pdd) + len(questions_auto) + len(questions_car)
    
    total_games = sum(profile.get('pdd_games', 0) + 
                     profile.get('auto_games', 0) + 
                     profile.get('car_quiz_games', 0) +
                     profile.get('random_games', 0) +
                     profile.get('exam_games', 0)
                     for profile in users_data.values())
    
    total_answers = sum(profile.get('correct_answers', 0) + 
                       profile.get('wrong_answers', 0)
                       for profile in users_data.values())
    
    stats_text = (
        "📊 <b>Статистика бота AutoQuiz</b>\n\n"
        f"👥 Всего пользователей: {total_users}\n"
        f"❓ Всего вопросов: {total_questions}\n"
        f"🎮 Всего игр: {total_games}\n"
        f"📝 Всего ответов: {total_answers}\n\n"
        f"📚 Вопросов ПДД: {len(questions_pdd)}\n"
        f"🚗 Автофактов: {len(questions_auto)}\n"
        f"🚘 Фото-викторина: {len(questions_car)}"
    )
    
    return stats_text

def load_questions():
    """загружает вопросы из json файлов"""
    global questions_pdd, questions_auto, questions_car
    
    def safe_load_json(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logging.info(f"Загружено {len(data)} элементов из {filepath}")
            return data
        except FileNotFoundError:
            logging.error(f"Файл не найден: {filepath}")
            return []
        except json.JSONDecodeError:
            logging.error(f"Ошибка формата JSON: {filepath}")
            return []
        except Exception as e:
            logging.error(f"Ошибка загрузки {filepath}: {e}")
            return []
    
    questions_pdd = safe_load_json(QUESTIONS_PDD)
    questions_auto = safe_load_json(QUESTIONS_AUTO)
    questions_car = safe_load_json(CAR_QUIZ)

# ФУНКЦИИ СОЗДАНИЯ КЛАВИАТУР

def create_answer_keyboard(question, question_index, is_exam=False, is_car_quiz=False):
    """создает клавиатуру с вариантами ответов"""
    buttons = []
    for i, answer in enumerate(question['answers']):
        if is_exam:
            callback_data = f"exam_answer_{question_index}_{i}"
        elif is_car_quiz:
            callback_data = f"car_answer_{question_index}_{i}"
        else:
            callback_data = f"answer_{question_index}_{i}"
        
        button = InlineKeyboardButton(
            text=answer,
            callback_data=callback_data
        )
        buttons.append([button])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard

def get_main_menu():
    """создает главное меню бота"""
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

# ФУНКЦИИ ОТПРАВКИ ВОПРОСОВ 

async def send_question(chat_id, mode):
    """отправляет вопрос пользователю"""
    if mode == "pdd":
        if not questions_pdd:
            await bot.send_message(chat_id, "❌ Вопросы ПДД не загружены")
            return
        questions_list = questions_pdd
        emoji = "🚦"
    elif mode == "auto":
        if not questions_auto:
            await bot.send_message(chat_id, "❌ Автофакты не загружены")
            return
        questions_list = questions_auto
        emoji = "🚗"
    elif mode == "random":
        all_q = questions_pdd + questions_auto
        if not all_q:
            await bot.send_message(chat_id, "❌ Вопросы не загружены")
            return
        questions_list = all_q
        emoji = "🎲"
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

async def send_car_question(chat_id):
    """отправляет вопрос с фото машины"""
    if not questions_car:
        await bot.send_message(
            chat_id,
            "❌ Вопросы с машинами не загружены.\nПроверь файл car_quiz.json"
        )
        return
    
    question = random.choice(questions_car)
    question_index = questions_car.index(question)
    
    user_games[chat_id] = {
        "mode": "car_quiz",
        "question": question,
        "question_index": question_index,
        "questions_list": questions_car
    }
    
    image_path = question.get('image', '')
    
    try:
        photo = FSInputFile(image_path)
        
        await bot.send_photo(
            chat_id,
            photo=photo,
            caption=f"🚘 <b>{question['question']}</b>",
            parse_mode="HTML",
            reply_markup=create_answer_keyboard(question, question_index, is_car_quiz=True)
        )
    except FileNotFoundError:
        logging.error(f"Фото не найдено: {image_path}")
        await bot.send_message(
            chat_id,
            f"🚘 <b>{question['question']}</b>\n\n❌ Фото не найдено: {image_path}",
            parse_mode="HTML",
            reply_markup=create_answer_keyboard(question, question_index, is_car_quiz=True)
        )
    except Exception as e:
        logging.error(f"Ошибка отправки фото: {e}")
        await bot.send_message(
            chat_id,
            f"🚘 <b>{question['question']}</b>\n\n(фото не загрузилось)",
            parse_mode="HTML",
            reply_markup=create_answer_keyboard(question, question_index, is_car_quiz=True)
        )

# ФУНКЦИИ ПРОВЕРКИ ОТВЕТОВ 

async def check_answer(callback: types.CallbackQuery, question_index, answer_index):
    """проверяет ответ на обычный вопрос"""
    chat_id = callback.message.chat.id
    user_id = callback.from_user.id
    username = callback.from_user.username or callback.from_user.first_name
    
    if not check_spam(user_id):
        await callback.answer("⚠️ Не так быстро!", show_alert=True)
        return
    
    get_user_profile(user_id, username)
    
    if chat_id not in user_games:
        await callback.message.answer("❌ Нет активной игры. Начни новую через /start")
        return
    
    game = user_games[chat_id]
    question = game['question']
    
    is_correct = (answer_index == question['correct'])
    
    if is_correct:
        points = POINTS_CORRECT
        phrase = random.choice(positive_phrases)
        result_text = f"✅ <b>{phrase}</b>\n\n💰 +{points} очков"
    else:
        points = POINTS_WRONG
        phrase = random.choice(negative_phrases)
        correct_answer = question['answers'][question['correct']]
        result_text = f"❌ <b>Неправильно!</b>\n\n"
        result_text += f"✔️ Правильный ответ: <b>{correct_answer}</b>\n\n"
        result_text += f"{phrase}\n💸 {points} очков"
    
    update_user_score(user_id, points, is_correct, game['mode'])
    
    profile = users_data[str(user_id)]
    result_text += f"\n\n📊 Всего очков: <b>{profile['total_score']}</b>"
    
    await callback.message.answer(result_text, parse_mode="HTML")
    
    del user_games[chat_id]
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➡️ Следующий вопрос", callback_data=f"mode_{game['mode']}")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ])
    
    await callback.message.answer("Что дальше?", reply_markup=keyboard)

async def check_car_answer(callback: types.CallbackQuery, question_index, answer_index):
    """проверяет ответ на фото-викторину"""
    chat_id = callback.message.chat.id
    user_id = callback.from_user.id
    username = callback.from_user.username or callback.from_user.first_name
    
    if not check_spam(user_id):
        await callback.answer("⚠️ Не так быстро!", show_alert=True)
        return
    
    get_user_profile(user_id, username)
    
    if chat_id not in user_games:
        await callback.message.answer("❌ Нет активной игры. Начни новую через /start")
        return
    
    game = user_games[chat_id]
    question = game['question']
    
    is_correct = (answer_index == question['correct'])
    
    if is_correct:
        points = POINTS_CORRECT
        phrase = random.choice(positive_phrases)
        result_text = f"✅ <b>{phrase}</b>\n\n💰 +{points} очков"
    else:
        points = POINTS_WRONG
        phrase = random.choice(negative_phrases)
        correct_answer = question['answers'][question['correct']]
        result_text = f"❌ <b>Неправильно!</b>\n\n"
        result_text += f"✔️ Правильный ответ: <b>{correct_answer}</b>\n\n"
        result_text += f"{phrase}\n💸 {points} очков"
    
    update_user_score(user_id, points, is_correct, "car_quiz")
    
    profile = users_data[str(user_id)]
    result_text += f"\n\n📊 Всего очков: <b>{profile['total_score']}</b>"
    
    await callback.message.answer(result_text, parse_mode="HTML")
    
    del user_games[chat_id]
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➡️ Следующее фото", callback_data="mode_car_quiz")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ])
    
    await callback.message.answer("Что дальше?", reply_markup=keyboard)

# ФУНКЦИИ ЭКЗАМЕНА 

async def start_exam(chat_id, user_id):
    """начинает экзамен"""
    all_questions = questions_pdd + questions_auto
    
    if not all_questions:
        await bot.send_message(chat_id, "❌ Вопросы не загружены. Проверь файлы данных.")
        return
    
    exam_questions = random.sample(all_questions, min(EXAM_QUESTIONS_COUNT, len(all_questions)))
    
    user_exams[chat_id] = {
        "questions": exam_questions,
        "current_index": 0,
        "correct_count": 0,
        "wrong_count": 0,
        "user_id": user_id
    }
    
    logging.info(f"Пользователь ID:{user_id} начал экзамен")
    await send_exam_question(chat_id)

async def send_exam_question(chat_id):
    """отправляет вопрос экзамена"""
    if chat_id not in user_exams:
        return
    
    exam = user_exams[chat_id]
    current_index = exam['current_index']
    
    if current_index >= len(exam['questions']):
        await finish_exam(chat_id)
        return
    
    question = exam['questions'][current_index]
    
    question_text = (
        f"🏁 <b>ЭКЗАМЕН</b>\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"Вопрос {current_index + 1} из {len(exam['questions'])}\n\n"
        f"{question['question']}"
    )
    
    await bot.send_message(
        chat_id,
        question_text,
        parse_mode="HTML",
        reply_markup=create_answer_keyboard(question, current_index, is_exam=True)
    )

async def finish_exam(chat_id):
    """завершает экзамен и показывает результаты"""
    if chat_id not in user_exams:
        return
    
    exam = user_exams[chat_id]
    user_id = exam['user_id']
    
    total_points = (exam['correct_count'] * POINTS_CORRECT) + (exam['wrong_count'] * POINTS_WRONG)
    
    user_id_str = str(user_id)
    if user_id_str in users_data:
        profile = users_data[user_id_str]
        profile['total_score'] += total_points
        profile['exam_games'] = profile.get('exam_games', 0) + 1
        
        if exam['correct_count'] >= (len(exam['questions']) * 0.7):
            profile['exams_passed'] = profile.get('exams_passed', 0) + 1
        
        save_users()
    
    total_questions = len(exam['questions'])
    percentage = (exam['correct_count'] / total_questions) * 100
    
    logging.info(f"Пользователь ID:{user_id} завершил экзамен. Результат: {percentage:.1f}%")
    
    result_text = (
        f"╔═══════════════════╗\n"
        f"🏁 <b>ЭКЗАМЕН ЗАВЕРШЕН!</b>\n"
        f"╚═══════════════════╝\n\n"
        f"📊 <b>Результаты:</b>\n"
        f"✅ Правильно: {exam['correct_count']}/{total_questions}\n"
        f"❌ Ошибок: {exam['wrong_count']}\n"
        f"📈 Процент: {percentage:.1f}%\n\n"
    )
    
    if percentage >= 90:
        result_text += "🏆 <b>ОТЛИЧНО!</b>\nТы настоящий профи! 🚀\n"
    elif percentage >= 70:
        result_text += "👍 <b>ХОРОШО!</b>\nТы молодец! 💪\n"
    elif percentage >= 50:
        result_text += "😐 <b>УДОВЛЕТВОРИТЕЛЬНО</b>\nМожно лучше! 📚\n"
    else:
        result_text += "😔 <b>НЕ СДАЛ</b>\nПопробуй еще раз! 🔄\n"
    
    result_text += f"\n💰 Заработано: <b>{total_points}</b> очков\n"
    
    if user_id_str in users_data:
        result_text += f"📊 Всего очков: <b>{users_data[user_id_str]['total_score']}</b>"
    
    await bot.send_message(chat_id, result_text, parse_mode="HTML")
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Пройти еще раз", callback_data="mode_exam")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ])
    
    await bot.send_message(chat_id, "Что дальше?", reply_markup=keyboard)
    
    del user_exams[chat_id]

# обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """обработчик команды /start"""
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    get_user_profile(user_id, username)
    
    logging.info(f"Пользователь {username} (ID: {user_id}) запустил бота")
    
    # приветственное сообщение
    welcome_text = (
        "🚗 <b>Привет! Это AutoQuiz!</b>\n\n"
        "🏁 Викторина про ПДД и автомобили,\n"
        "где ты можешь прокачать свои знания или же просто проверить их!\n\n"
        "Выбери режим игры:"
    )
    await message.answer(welcome_text, parse_mode="HTML", reply_markup=get_main_menu())

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    """обработчик команды /help"""
    help_text = (
        "📖 <b>Помощь по боту AutoQuiz</b>\n\n"
        "<b>Команды:</b>\n"
        "/start - запустить бота\n"
        "/help - показать эту справку\n"
        "/stats - статистика бота\n\n"
        "<b>Режимы игры:</b>\n"
        "🚦 <b>Тест ПДД</b> - вопросы по правилам дорожного движения\n"
        "🚗 <b>Автофакты</b> - интересные факты об автомобилях\n"
        "🚘 <b>Угадай машину</b> - узнай марку по фото\n"
        "🎲 <b>Случайная викторина</b> - микс всех вопросов\n"
        "🏁 <b>Экзамен</b> - 20 вопросов подряд\n\n"
        "<b>Система очков:</b>\n"
        f"✅ Правильный ответ: +{POINTS_CORRECT} очков\n"
        f"❌ Неправильный ответ: {POINTS_WRONG} очков\n\n"
        "<b>Профиль:</b>\n"
        "Смотри свою статистику и прогресс\n"
        "Сбрасывай очки если нужно начать заново\n\n"
        "<b>Рейтинг:</b>\n"
        "Соревнуйся с другими игроками!\n"
        "Попади в топ-10! 🏆"
    )
    
    await message.answer(help_text, parse_mode="HTML")
    logging.info(f"Пользователь ID:{message.from_user.id} запросил помощь")

@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    """обработчик команды /stats"""
    stats_text = get_bot_stats()
    await message.answer(stats_text, parse_mode="HTML")
    logging.info(f"Пользователь ID:{message.from_user.id} запросил статистику")

# ОБРАБОТЧИК ЗАПРОСОВ

@dp.callback_query()
async def handle_callback(callback: types.CallbackQuery):
    """обработчик нажатий на кнопки"""
    data = callback.data
    chat_id = callback.message.chat.id
    user_id = callback.from_user.id
    
    if data == "main_menu":
        welcome_text = "🚗 <b>AutoQuiz</b>\n\nВыбери режим игры:"
        await callback.message.answer(welcome_text, parse_mode="HTML", reply_markup=get_main_menu())
    
    elif data == "mode_pdd":
        logging.info(f"Пользователь ID:{user_id} выбрал режим ПДД")
        await callback.message.answer(
            "🚦 <b>Тест ПДД</b>\n\n"
            "Проверь свои знания правил дорожного движения!\n"
            "Готов? Поехали! 🚗",
            parse_mode="HTML"
        )
        await send_question(chat_id, "pdd")
    
    elif data == "mode_auto":
        logging.info(f"Пользователь ID:{user_id} выбрал режим Автофакты")
        await callback.message.answer(
            "🚗 <b>Автофакты</b>\n\n"
            "Узнай интересные факты о машинах!\n"
            "Поехали! 🏎️",
            parse_mode="HTML"
        )
        await send_question(chat_id, "auto")
    
    elif data == "mode_car_quiz":
        logging.info(f"Пользователь ID:{user_id} выбрал режим Угадай машину")
        await callback.message.answer(
            "🚘 <b>Угадай машину по фото</b>\n\n"
            "Смотри на фото и выбирай правильную марку!\n"
            "Покажи свои знания! 📸",
            parse_mode="HTML"
        )
        await send_car_question(chat_id)
    
    elif data == "mode_random":
        logging.info(f"Пользователь ID:{user_id} выбрал режим Случайная викторина")
        await callback.message.answer(
            "🎲 <b>Случайная викторина</b>\n\n"
            "Вопросы из разных тем!\n"
            "Будь готов ко всему! 🔥",
            parse_mode="HTML"
        )
        await send_question(chat_id, "random")
    
    elif data == "mode_exam":
        await callback.message.answer(
            f"🏁 <b>Режим Экзамена</b>\n\n"
            f"Тебя ждет {EXAM_QUESTIONS_COUNT} вопросов подряд!\n"
            f"Покажи все свои знания!\n"
            f"Готов? Поехали! 🚀",
            parse_mode="HTML"
        )
        await start_exam(chat_id, user_id)
    
    elif data == "profile":
        profile_text = get_profile_text(user_id)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Сбросить прогресс", callback_data="reset_progress")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
        ])
        
        await callback.message.answer(profile_text, parse_mode="HTML", reply_markup=keyboard)
    
    elif data == "reset_progress":
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Да, сбросить", callback_data="reset_confirm")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="profile")]
        ])
        
        await callback.message.answer(
            "⚠️ <b>Внимание!</b>\n\n"
            "Ты уверен, что хочешь сбросить весь прогресс?\n"
            "Все очки и статистика будут удалены!\n\n"
            "Это действие нельзя отменить!",
            parse_mode="HTML",
            reply_markup=keyboard
        )
    
    elif data == "reset_confirm":
        if reset_user_progress(user_id):
            await callback.message.answer(
                "✅ <b>Прогресс сброшен!</b>\n\n"
                "Теперь можешь начать заново!\n"
                "Удачи! 🍀",
                parse_mode="HTML",
                reply_markup=get_main_menu()
            )
        else:
            await callback.message.answer("❌ Ошибка сброса прогресса")
    
    elif data == "rating":
        rating_text = get_rating_text()
        await callback.message.answer(rating_text, parse_mode="HTML")
    
    elif data.startswith("answer_"):
        parts = data.split("_")
        question_index = int(parts[1])
        answer_index = int(parts[2])
        await check_answer(callback, question_index, answer_index)
    
    elif data.startswith("car_answer_"):
        parts = data.split("_")
        question_index = int(parts[2])
        answer_index = int(parts[3])
        await check_car_answer(callback, question_index, answer_index)
    
    elif data.startswith("exam_answer_"):
        parts = data.split("_")
        answer_index = int(parts[3])
        
        if chat_id in user_exams:
            exam = user_exams[chat_id]
            current_question = exam['questions'][exam['current_index']]
            
            is_correct = (answer_index == current_question['correct'])
            
            if is_correct:
                exam['correct_count'] += 1
                await callback.message.answer("✅ Правильно!")
            else:
                exam['wrong_count'] += 1
                correct_answer = current_question['answers'][current_question['correct']]
                await callback.message.answer(f"❌ Неправильно!\n✔️ Правильный ответ: {correct_answer}")
            
            exam['current_index'] += 1
            await send_exam_question(chat_id)
    
    await callback.answer()

# главная функция запуска бота
async def main():
    # проверка наличия папки data
    if not os.path.exists('data'):
        logging.warning("Папка data не найдена, создаю...")
        os.makedirs('data', exist_ok=True)
    
    # загрузка данных
    load_questions()
    load_users()
    
    # проверка что хотя бы некоторые вопросы загружены
    if not questions_pdd and not questions_auto and not questions_car:
        logging.error("⚠️ ВНИМАНИЕ: Не загружено ни одного вопроса! Проверь файлы данных.")
    
    logging.info("🤖 Бот AutoQuiz запущен и готов к работе!")
    
    await dp.start_polling(bot)

# запуск программы
if __name__ == "__main__":
    asyncio.run(main())



