import datetime
import orjson
import time
import hashlib
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.filters.command import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiofile import async_open
from calendar import monthrange
from pathlib import Path
from source.Bot.messages import stats_msg, get_rqst_msg
from source.Bot.dates import months, months_id
from source.Analyzer.AnalyzerDataTypes import from_dict
from source.Analyzer.AnalyzerDataTypes import SharesPortfolioIntervalConnectorRequest, SharesPortfolioIntervalAnalyzerResponse
from source.Bot.request_former import form_request
from source.Bot.result_former import form_result
from source.Router.db_interaction import get_token_by_user_id
from source.Bot.encoder import token_encoder

router = Router()

class Request(StatesGroup):
    encoded_token = State()
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
    encoded_token = get_token_by_user_id(str(message.from_user.id))
    if encoded_token is None:
        builder = ReplyKeyboardBuilder()
        builder.add(types.KeyboardButton(text="Помощь"))
        builder.add(types.KeyboardButton(text="Войти"))
        builder.adjust(2)
        await message.reply("Пожалуйста, войдите перед тем, как запрашивать статистику, или повторите попытку позже",
                            reply_markup=builder.as_markup(resize_keyboard=True))
        return
    await state.update_data(encoded_token=encoded_token)
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
    await state.update_data(security_type=message.text.lower())
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
    await message.answer("К сожалению, Ваш запрос пока не поддерживается")
    # TODO: add request processing


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
    data = await state.get_data()
    month_len = monthrange(data["start_year"], data["start_month"])[1]
    for i in range(1, month_len + 1):
        builder.add(types.KeyboardButton(text=str(i)))
    builder.adjust(5, 5, 5, 5, 5, month_len - 25)
    await message.reply("Отлично\! Теперь выберите число начала",
                         reply_markup=builder.as_markup(resize_keyboard=True,
                                                        input_field_placeholder="Число начала",
                                                        one_time_keyboard=True))

@router.message(Request.start_date, lambda message: message.text.isdigit())
async def get_start_date(message: types.Message, state: FSMContext):
    data = await state.get_data()
    month_len = monthrange(data["start_year"], data["start_month"])[1]
    if 1 <= int(message.text) <= month_len:
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
        for i in range(1, month_len + 1):
            builder.add(types.KeyboardButton(text=str(i)))
        builder.adjust(5, 5, 5, 5, 5, month_len - 25)
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
    data = await state.get_data()
    month_len = monthrange(data["end_year"], data["end_month"])[1]
    for i in range(1, month_len + 1):
        builder.add(types.KeyboardButton(text=str(i)))
    builder.adjust(5, 5, 5, 5, 5, month_len - 25)
    await message.reply("Отлично\! Теперь выберите число окончания",
                         reply_markup=builder.as_markup(resize_keyboard=True,
                                                        input_field_placeholder="Число окончания",
                                                        one_time_keyboard=True))

@router.message(Request.end_date, lambda message: message.text.isdigit())
async def get_end_date(message: types.Message, state: FSMContext):
    data = await state.get_data()
    month_len = monthrange(data["end_year"], data["end_month"])[1]
    if 1 <= int(message.text) <= month_len:
        await state.update_data(end_date=int(message.text))
        data = await state.get_data()
        if data["start_year"] is not None:
            request = await form_request(data["security_type"],
                                         datetime.date(data["start_year"], data["start_month"], data["start_date"]),
                                         datetime.date(data["end_year"], data["end_month"], data["end_date"]))
            request.token_cypher = data["encoded_token"]
            request_time_str = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
            request_file_name = f"request_shares_{hashlib.sha256((request.token_cypher+request_time_str).encode('utf-8')).hexdigest()}.json"
            request_path = "../../connector_requests/" + request_file_name
            async with async_open(request_path, 'wb') as f:
                await f.write(orjson.dumps(request))
            response_file_name = f"response_shares_{hashlib.sha256((request.token_cypher + request_time_str).encode('utf-8')).hexdigest()}.json"
            response_path = "../../analyzer_responses/" + response_file_name
            results = None
            total_sleep_time = 0
            while not results and total_sleep_time < 10:
                time.sleep(0.5)
                total_sleep_time += 0.5
                if Path(response_path).exists():
                    async with async_open(response_path, 'rb') as f:
                        contents = await f.read()
                        results = from_dict(SharesPortfolioIntervalAnalyzerResponse, orjson.loads(contents))
            Path(response_path).unlink()
            if not results:
                await message.answer("К сожалению, Ваш запрос не удалось обработать\. Попробуйте позже или скорректируйте запрос")
            else:
                result_msg = await form_result(results)
                await message.answer(result_msg)
        else:
            await message.answer("К сожалению, Ваш запрос пока не поддерживается")
            # TODO: add request processing
        await state.clear()
    else:
        builder = ReplyKeyboardBuilder()
        for i in range(1, month_len + 1):
            builder.add(types.KeyboardButton(text=str(i)))
        builder.adjust(5, 5, 5, 5, 5, month_len - 25)
        await message.reply("Выберите корректную дату окончания",
                            reply_markup=builder.as_markup(resize_keyboard=True,
                                                           input_field_placeholder="Число окончания",
                                                           one_time_keyboard=True))
