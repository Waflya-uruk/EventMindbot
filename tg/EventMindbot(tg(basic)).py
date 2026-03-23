import logging
import os
import speech_recognition as sr
from pydub import AudioSegment
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.utils.keyboard import ReplyKeyboardBuilder
import asyncio

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = "8794559839:AAEWpvprA0hm6TruWlNqnnOK0FCHHznzJ7E"

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

class BotStates(StatesGroup):
    START = State()
    GET_MAIL = State()
    GET_PASS = State()
    MAIN_MENU = State()
    AI_ASSISTANT = State()

def get_start_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="Вход"))
    builder.add(KeyboardButton(text="Регистрация"))
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

def get_main_menu_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="AI ассистент"))
    builder.add(KeyboardButton(text="Расписание"))
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

def get_ai_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="Назад"))
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)

def get_back_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="Назад"))
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)

# Функция для распознавания голоса
async def recognize_speech(ogg_file_path):
    """
    Конвертирует OGG в WAV и распознает речь
    """
    wav_file_path = ogg_file_path.replace('.ogg', '.wav')
    
    try:
        audio = AudioSegment.from_ogg(ogg_file_path)
        audio.export(wav_file_path, format="wav")
        
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_file_path) as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio_data = recognizer.record(source)
            
            try:
                text = recognizer.recognize_google(audio_data, language="ru-RU")
                return text, None
            except sr.UnknownValueError:
                return None, "Не удалось распознать речь"
            except sr.RequestError as e:
                return None, f"Ошибка сервиса распознавания: {e}"
                
    except Exception as e:
        return None, f"Ошибка при обработке аудио: {e}"
    finally:
        if os.path.exists(wav_file_path):
            os.remove(wav_file_path)

# /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.set_state(BotStates.START)
    await message.answer(
        "Добро пожаловать!\nВыберите действие:",
        reply_markup=get_start_keyboard()
    )

# Обработка начального меню
@dp.message(BotStates.START, F.text)
async def handle_start(message: types.Message, state: FSMContext):
    text = message.text
    
    if text == "Вход":
        await state.set_state(BotStates.MAIN_MENU)
        await message.answer(
            "Добро пожаловать в главное меню!",
            reply_markup=get_main_menu_keyboard()
        )
    
    elif text == "Регистрация":
        await state.set_state(BotStates.GET_MAIL)
        await message.answer(
            "Введите ваш email:",
            reply_markup=get_back_keyboard()
        )
    
    else:
        await message.answer(
            "Пожалуйста, используйте кнопки.",
            reply_markup=get_start_keyboard()
        )

# Регистрация: получение email
@dp.message(BotStates.GET_MAIL, F.text)
async def handle_get_mail(message: types.Message, state: FSMContext):
    text = message.text
    
    if text == "Назад":
        await state.set_state(BotStates.START)
        await message.answer(
            "Выберите действие:",
            reply_markup=get_start_keyboard()
        )
    else:
        await state.update_data(email=text)
        await state.set_state(BotStates.GET_PASS)
        await message.answer(
            "Введите ваш пароль:",
            reply_markup=get_back_keyboard()
        )

# Регистрация: получение пароля
@dp.message(BotStates.GET_PASS, F.text)
async def handle_get_pass(message: types.Message, state: FSMContext):
    text = message.text
    
    if text == "Назад":
        await state.set_state(BotStates.GET_MAIL)
        await message.answer(
            "Введите ваш email:",
            reply_markup=get_back_keyboard()
        )
    else:
        data = await state.get_data()
        email = data.get('email')
        
        await state.set_state(BotStates.START)
        await message.answer(
            f"✅ Регистрация завершена!\n\n"
            f"Email: {email}\n"
            f"Пароль: {text}\n\n"
            f"Теперь вы можете войти.",
            reply_markup=get_start_keyboard()
        )

# Главное меню
@dp.message(BotStates.MAIN_MENU, F.text)
async def handle_main_menu(message: types.Message, state: FSMContext):
    text = message.text
    
    if text == "AI ассистент":
        await state.set_state(BotStates.AI_ASSISTANT)
        await message.answer(
            "🤖 AI ассистент\n\nОтправьте текст или голосовое сообщение:",
            reply_markup=get_ai_keyboard()
        )
    
    elif text == "Расписание":
        await message.answer(
            "📅 ВЫВОД ЗАПЛАНИРОВАННЫХ УВЕДОМЛЕНИЙ О МЕРОПРИЯТИИ:\n\n"
            "• Встреча с командой - 20.03.2026\n"
            "• Презентация проекта - 25.03.2026\n"
            "• Планерка - 27.03.2026"
        )
        await message.answer(
            "Главное меню:",
            reply_markup=get_main_menu_keyboard()
        )
    
    else:
        await message.answer(
            "Выберите пункт меню:",
            reply_markup=get_main_menu_keyboard()
        )

# AI ассистент - обработка текста
@dp.message(BotStates.AI_ASSISTANT, F.text)
async def handle_ai_text(message: types.Message, state: FSMContext):
    text = message.text
    if text == "Назад":
        await state.set_state(BotStates.MAIN_MENU)
        await message.answer(
            "Главное меню:",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    await message.answer(
        f"✅ Текстовый запрос принят: \"{text}\"\n\n"
        f"(здесь будет ответ AI ассистента)",
        reply_markup=get_ai_keyboard()
    )

# AI ассистент - обработка голоса
@dp.message(BotStates.AI_ASSISTANT, F.voice)
async def handle_ai_voice(message: types.Message, state: FSMContext):
    voice = message.voice
    processing_msg = await message.answer(
        "🎤 Получил голосовое сообщение. Обрабатываю..."
    )
    
    file = await bot.get_file(voice.file_id)
    ogg_file_path = f"voice_{voice.file_id}.ogg"
    await bot.download_file(file.file_path, ogg_file_path)
    
    try:
        text, error = await recognize_speech(ogg_file_path)
        
        if text:
            await processing_msg.edit_text(
                f"✅ Распознанный текст: \"{text}\"\n\n"
                f"(здесь будет ответ AI ассистента)"
            )
        else:
            await processing_msg.edit_text(
                f"❌ {error}\n\n"
                f"Попробуйте отправить еще раз или используйте текст."
            )
            
    except Exception as e:
        await processing_msg.edit_text(
            f"❌ Ошибка при обработке: {str(e)}"
        )
    finally:
        if os.path.exists(ogg_file_path):
            os.remove(ogg_file_path)
    await message.answer(
        "Отправьте еще сообщение или нажмите 'Назад'",
        reply_markup=get_ai_keyboard()
    )

@dp.message()
async def handle_unknown(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    
    if current_state is None:
        await message.answer(
            "Используйте /start для начала работы"
        )
    else:
        await message.answer(
            "Пожалуйста, используйте кнопки или отправьте текст/голос"
        )

@dp.message(Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "До свидания! Для начала работы нажмите /start",
        reply_markup=ReplyKeyboardRemove()
    )

async def main():
    print("Бот запущен! Нажмите Ctrl+C для остановки.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
