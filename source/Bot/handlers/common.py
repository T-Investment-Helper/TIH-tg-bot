from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.filters.command import Command
from aiogram.fsm.state import default_state
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from source.Bot.messages import start_msg, help_msg

router = Router()

@router.message(F.text, Command("start"))
async def cmd_start(message: types.Message):
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="Войти"))
    builder.add(types.KeyboardButton(text="Статистика"))
    builder.add(types.KeyboardButton(text="Помощь"))
    builder.adjust(2, 1)
    await message.answer(start_msg,
                         reply_markup=builder.as_markup(resize_keyboard=True,
                                                        input_field_placeholder="Выбор за Вами...",
                                                        one_time_keyboard=True)
                         )

@router.message(F.text, Command("help"))
@router.message(F.text.lower() == "помощь")
async def cmd_help(message: types.Message):
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="Войти"))
    builder.add(types.KeyboardButton(text="Статистика"))
    builder.adjust(2)
    await message.answer(help_msg,
                         reply_markup=builder.as_markup(resize_keyboard=True,
                                                        input_field_placeholder="Выбор за Вами...",
                                                        one_time_keyboard=True)
                         )

@router.message(F.text, Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    if state == default_state:
        await state.set_data({})
    else:
        await state.clear()
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="Войти"))
    builder.add(types.KeyboardButton(text="Статистика"))
    builder.adjust(2)
    await message.reply(
        text="Действия отменены",
        reply_markup=builder.as_markup(resize_keyboard=True,
                                       input_field_placeholder="Выбор за Вами...",
                                       one_time_keyboard=True)
    )