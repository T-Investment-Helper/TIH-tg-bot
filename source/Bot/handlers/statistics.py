import datetime
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.filters.command import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from source.Bot.messages import stats_msg, get_rqst_msg
from source.Bot.dates import months, months_id, months_len

router = Router()

class Request(StatesGroup):
    security_type = State()
    request_type = State()
    start_year = State()
    start_month = State()
    start_date = State()
    end_year = State()
    end_month = State()
    end_date = State()

@router.message(F.text, Command("stats"))
@router.message(F.text.lower() == "статистика")
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

@router.message(F.text, Request.security_type, lambda message: message.text.lower() in ["акции"])
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

@router.message(Request.request_type, F.text.lower() == "с открытия счёта до текущей даты")
async def get_total_stats(message: types.Message, state: FSMContext):
    data = await state.get_data()
    # request = await form_request(data["security_type"])
    #TODO: process request


@router.message(Request.request_type, F.text.lower() == "с открытия счёта до определённой даты")
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

@router.message(Request.request_type, F.text.lower() == "за определённый период")
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

@router.message(Request.start_year, lambda message: message.text.isdigit())
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

@router.message(Request.start_month, lambda message: message.text.upper() in months)
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

@router.message(Request.start_date, lambda message: message.text.isdigit())
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

@router.message(Request.end_year, lambda message: message.text.isdigit())
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

@router.message(Request.end_month, lambda message: message.text.upper() in months)
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

@router.message(Request.end_date, lambda message: message.text.isdigit())
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
