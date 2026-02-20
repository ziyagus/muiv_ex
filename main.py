import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# токен бота 
TOKEN_BOT = "token"

# создаем объекты бота и диспетчера
bot = Bot(token=TOKEN_BOT)
dp = Dispatcher()

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
    
    # отправляем приветствие
    await message.answer(welcome_text, parse_mode="HTML")

# главная функция запуска бота
async def main():
    # запуск бота
    print("Бот запущен!")
    await dp.start_polling(bot)

# запуск программы
if __name__ == "__main__":
    asyncio.run(main())


