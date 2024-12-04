import asyncio
import datetime
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.client.default import DefaultBotProperties
from aiogram.filters.command import Command
from aiogram.fsm.state import State, StatesGroup, default_state
from aiogram.enums import ParseMode
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from config_getter import config
from encoder import token_encoder
from dates import months, months_id, months_len
from messages import start_msg, sign_in_msg, get_confirm_msg, help_msg, stats_msg, get_rqst_msg
# from request_former import form_request
# from source.Analyzer.AnalyzerDataTypes import SharesPortfolioIntervalConnectorRequest

logging.basicConfig(level=logging.INFO)

#TODO: choose a more optimal storage
storage = MemoryStorage()

bot = Bot(
    token=config.bot_token.get_secret_value(),
    default=DefaultBotProperties(
        parse_mode=ParseMode.MARKDOWN_V2
    ),
    storage=storage
)

dp = Dispatcher()

@dp.message(F.text, Command("start"))
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

@dp.message(F.text, Command("help"))
@dp.message(F.text.lower() == "помощь")
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

class User(StatesGroup):
    id = State()
    token = State()
    confirmation = State()

@dp.message(F.text, Command("cancel"))
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

@dp.message(F.text.lower() == "войти")
async def sign_in(message: types.Message, state: FSMContext):
    await state.update_data(id=message.from_user.id)
    await state.set_state(User.token)
    await message.reply(sign_in_msg)

@dp.message(User.token, F.text)
async def get_token(message: types.Message, state: FSMContext):
    token = message.text
    await state.update_data(token=token)
    await state.set_state(User.confirmation)
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="Подтвердить"))
    builder.add(types.KeyboardButton(text="Не подтверждать"))
    builder.adjust(2)
    await message.reply(f'''Подтвердите, пожалуйста, отправку токена {token}, нажав кнопку "Подтвердить" \
или написав "Подтвердить" \(в любом регистре\)\.

Обратите внимание, что это последний шанс стереть введённый токен, написав /cancel\! После \
подтверждения зашифрованный токен будет внесён в базу данных, изменить его можно будет только \
войдя заново\.''',
                        reply_markup=builder.as_markup(resize_keyboard=True))

@dp.message(User.confirmation, F.text)
async def get_confirmation(message: types.Message, state: FSMContext):
    if message.text.lower() == "подтвердить":
        data = await state.get_data()
        encoded_token = token_encoder.encode_token(data["token"])
        # TODO add (contact, encoded_token) to db

        builder = ReplyKeyboardBuilder()
        builder.add(types.KeyboardButton(text="Помощь"))
        builder.add(types.KeyboardButton(text="Статистика"))
        await message.reply(get_confirm_msg,
                            reply_markup=builder.as_markup(resize_keyboard=True))
        await state.clear()
    else:
        builder = ReplyKeyboardBuilder()
        builder.add(types.KeyboardButton(text="Подтвердить"))
        builder.add(types.KeyboardButton(text="Не подтверждать"))
        builder.adjust(2)
        await message.reply(f'''Подтвердите, пожалуйста, отправку токена, нажав кнопку "Подтвердить" \
        или написав "Подтвердить" \(в любом регистре\), или сотрите его, написав /cancel''',
                            reply_markup=builder.as_markup(resize_keyboard=True))


class Request(StatesGroup):
    security_type = State()
    request_type = State()
    start_year = State()
    start_month = State()
    start_date = State()
    end_year = State()
    end_month = State()
    end_date = State()

@dp.message(F.text, Command("stats"))
@dp.message(F.text.lower() == "статистика")
async def cmd_stats(message: types.Message, state: FSMContext):
    # TODO check if user id is registered
    await state.set_state(Request.security_type)
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="Акции"))
    # TODO: add more securities
    await message.answer(stats_msg,
                         reply_markup=builder.as_markup(resize_keyboard=True,
                                                        input_field_placeholder="Выбор за Вами...",
                                                        one_time_keyboard=True)
                         )

@dp.message(F.text, Request.security_type, lambda message: message.text.lower() in ["акции"])
async def get_request(message: types.Message, state: FSMContext):
    await state.update_data(security_type=message.text)
    await state.set_state(Request.request_type)
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="С открытия счёта до текущей даты"))
    builder.add(types.KeyboardButton(text="С открытия счёта до определённой даты"))
    builder.add(types.KeyboardButton(text="За определённый период"))
    builder.adjust(1, 1, 1)
    # TODO: add more request types
    await message.answer(get_rqst_msg,
                         reply_markup=builder.as_markup(resize_keyboard=True,
                                                        input_field_placeholder="Выбор за Вами...",
                                                        one_time_keyboard=True)
                         )

@dp.message(Request.request_type, F.text.lower() == "с открытия счёта до текущей даты")
async def get_total_stats(message: types.Message, state: FSMContext):
    data = await state.get_data()
    # request = await form_request(data["security_type"])
    #TODO: process request


@dp.message(Request.request_type, F.text.lower() == "с открытия счёта до определённой даты")
async def get_up_to_date_stats(message: types.Message, state: FSMContext):
    await state.update_data(start_year=None)
    await state.set_state(Request.end_year)
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text=str(datetime.date.today().year)))
    await message.answer('''Для получения статистики за период с открытия счёта \
до определённой даты, введите год \(или выберите текущий\) и выберите месяц и число окончания''',
                         reply_markup=builder.as_markup(resize_keyboard=True,
                                                        input_field_placeholder="Год окончания",
                                                        one_time_keyboard=True))

@dp.message(Request.request_type, F.text.lower() == "за определённый период")
async def get_period_stats(message: types.Message, state: FSMContext):
    await state.set_state(Request.start_year)
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text=str(datetime.date.today().year)))
    await message.reply('''Для получения статистики за определённый период \
сначала введите год \(или выберите текущий\) и выберите месяц и число его начала, \
затем введите год и выберите месяц и число его окончания''',
                         reply_markup=builder.as_markup(resize_keyboard=True,
                                                        input_field_placeholder="Год начала",
                                                        one_time_keyboard=True))

@dp.message(Request.start_year, lambda message: message.text.isdigit())
async def get_start_year(message: types.Message, state: FSMContext):
    await state.update_data(start_year=int(message.text))
    builder = ReplyKeyboardBuilder()
    for month in months:
        builder.add(types.KeyboardButton(text=month))
    builder.adjust(3, 3, 3, 3)
    await state.set_state(Request.start_month)
    await message.reply("Отлично\! Теперь выберите месяц начала",
                         reply_markup=builder.as_markup(resize_keyboard=True,
                                                        input_field_placeholder="Месяц начала",
                                                        one_time_keyboard=True))

@dp.message(Request.start_month, lambda message: message.text.upper() in months)
async def get_start_month(message: types.Message, state: FSMContext):
    await state.update_data(start_month=months_id[message.text.upper()])
    await state.set_state(Request.start_date)
    builder = ReplyKeyboardBuilder()
    for i in range(1, months_len[message.text.upper()] + 1):
        builder.add(types.KeyboardButton(text=str(i)))
    builder.adjust(5, 5, 5, 5, 5, months_len[message.text.upper()] - 25)
    await message.reply("Отлично\! Теперь выберите число начала",
                         reply_markup=builder.as_markup(resize_keyboard=True,
                                                        input_field_placeholder="Число начала",
                                                        one_time_keyboard=True))

@dp.message(Request.start_date, lambda message: message.text.isdigit())
async def get_start_date(message: types.Message, state: FSMContext):
    # TODO improve get_state
    date = await state.get_data()
    if 1 <= int(message.text) <= months_len[months[date["start_month"]]]:
        await state.update_data(start_date=int(message.text))
        await state.set_state(Request.end_year)
        builder = ReplyKeyboardBuilder()
        builder.add(types.KeyboardButton(text=str(datetime.date.today().year)))
        await message.reply("Отлично\! Теперь введите год окончания",
                            reply_markup=builder.as_markup(resize_keyboard=True,
                                                           input_field_placeholder="Год окончания",
                                                           one_time_keyboard=True))
    else:
        builder = ReplyKeyboardBuilder()
        for i in range(1, months_len[months[date["start_month"]]] + 1):
            builder.add(types.KeyboardButton(text=str(i)))
        builder.adjust(5, 5, 5, 5, 5, months_len[months[date["start_month"]]] - 25)
        await message.reply("Выберите корректную дату начала",
                            reply_markup=builder.as_markup(resize_keyboard=True,
                                                           input_field_placeholder="Число начала",
                                                           one_time_keyboard=True))

@dp.message(Request.end_year, lambda message: message.text.isdigit())
async def get_end_year(message: types.Message, state: FSMContext):
    await state.update_data(end_year=int(message.text))
    await state.set_state(Request.end_month)
    builder = ReplyKeyboardBuilder()
    for month in months:
        builder.add(types.KeyboardButton(text=month))
    builder.adjust(3, 3, 3, 3)
    await message.reply("Отлично\! Теперь выберите месяц окончания",
                        reply_markup=builder.as_markup(resize_keyboard=True,
                                                       input_field_placeholder="Месяц окончания",
                                                       one_time_keyboard=True))

@dp.message(Request.end_month, lambda message: message.text.upper() in months)
async def get_end_month(message: types.Message, state: FSMContext):
    await state.update_data(end_month=months_id[message.text.upper()])
    await state.set_state(Request.end_date)
    builder = ReplyKeyboardBuilder()
    for i in range(1, months_len[message.text.upper()] + 1):
        builder.add(types.KeyboardButton(text=str(i)))
    builder.adjust(5, 5, 5, 5, 5, months_len[message.text.upper()] - 25)
    await message.reply("Отлично\! Теперь выберите число окончания",
                         reply_markup=builder.as_markup(resize_keyboard=True,
                                                        input_field_placeholder="Число окончания",
                                                        one_time_keyboard=True))

@dp.message(Request.end_date, lambda message: message.text.isdigit())
async def get_end_date(message: types.Message, state: FSMContext):
    date = await state.get_data()
    if 1 <= int(message.text) <= months_len[months[date["end_month"]]]:
        await state.update_data(end_date=int(message.text))
        data = await state.get_data()
        # if data["start_year"] is not None:
            # request = await form_request(data["security_type"],
            #                             datetime.date(data["start_year"], data["start_month"], data["start_day"]),
            #                             datetime.date(data["end_year"], data["end_month"], data["end_day"]))
        # else:
            # request = await form_request(data["security_type"],
            #                             None,
            #                             datetime.date(data["end_year"], data["end_month"], data["end_day"]))
        # TODO: process request
        await state.clear()
    else:
        builder = ReplyKeyboardBuilder()
        for i in range(1, months_len[months[date["end_month"]]] + 1):
            builder.add(types.KeyboardButton(text=str(i)))
        builder.adjust(5, 5, 5, 5, 5, months_len[months[date["end_month"]]] - 25)
        await message.reply("Выберите корректную дату окончания",
                            reply_markup=builder.as_markup(resize_keyboard=True,
                                                           input_field_placeholder="Число окончания",
                                                           one_time_keyboard=True))


@dp.message()
async def unsupported_message(message: types.Message):
    await message.answer("Ваше сообщение застало нас врасплох, пожалуйста, \
отправьте поддерживаемую команду или напишите /help")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())