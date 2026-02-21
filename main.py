import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# токен бота
TOKEN_BOT = "token"

# создаем объекты бота и диспетчера
bot = Bot(token=TOKEN_BOT)
dp = Dispatcher()

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
    # приветственное сообщение
    welcome_text = (
        "🚗 <b>Привет! Это AutoQuiz!</b>\n\n"
        "🏁 Викторина про ПДД и автомобили,\n"
        "где ты можешь прокачать свои знания или же просто проверить их!\n\n"
        "Выбери режим игры:"
    )
    
    # отправляем приветствие с меню
    await message.answer(welcome_text, parse_mode="HTML", reply_markup=get_main_menu())

# обработчик нажатий на кнопки
@dp.callback_query()
async def handle_callback(callback: types.CallbackQuery):
    # получаем данные кнопки
    data = callback.data
    
    # пока просто ответ, что кнопка нажата, а дальше будет реализована обработка
    if data == "mode_pdd":
        await callback.message.answer("🚦 Режим 'Тест ПДД' (в разработке)")
    elif data == "mode_auto":
        await callback.message.answer("🚗 Режим 'Автофакты' (в разработке)")
    elif data == "mode_car_quiz":
        await callback.message.answer("🚘 Режим 'Угадай машину' (в разработке)")
    elif data == "mode_random":
        await callback.message.answer("🎲 Режим 'Случайная викторина' (в разработке)")
    elif data == "mode_exam":
        await callback.message.answer("🏁 Режим 'Экзамен' (в разработке)")
    elif data == "profile":
        await callback.message.answer("👤 Твой профиль (в разработке)")
    elif data == "rating":
        await callback.message.answer("🏆 Рейтинг игроков (в разработке)")
    
    # подтверждаем нажатие кнопки
    await callback.answer()

# главная функция запуска бота
async def main():
    # запуск бота
    print("Бот запущен!")
    await dp.start_polling(bot)

# запуск программы
if __name__ == "__main__":
    asyncio.run(main())



