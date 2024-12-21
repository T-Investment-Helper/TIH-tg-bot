import datetime
import orjson
import time
import hashlib
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.filters.callback_data import CallbackData
from aiogram.filters.command import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback, get_user_locale
from aiofile import async_open
from pathlib import Path
from source.Bot.messages import stats_msg, get_rqst_msg
from source.Analyzer.AnalyzerDataTypes import from_dict
from source.Analyzer.AnalyzerDataTypes import SharesPortfolioIntervalConnectorRequest, SharesPortfolioIntervalAnalyzerResponse
from source.Bot.request_former import form_request
from source.Bot.result_former import form_result
from source.Router.db_interaction import get_token_by_user_id
from source.Encoder.encoder import token_encoder

router = Router()

class Request(StatesGroup):
    encoded_token = State()
    security_type = State()
    request_type = State()
    start_date = State()
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
    await state.update_data(start_date=None)
    await state.set_state(Request.end_date)
    calendar = SimpleCalendar(
        locale=await get_user_locale(message.from_user), show_alerts=True
    )
    calendar.set_dates_range(datetime.datetime(2024, 1, 1), datetime.datetime.today()) # replace with portfolio creation
    await message.answer('''Для получения статистики за период с открытия счёта \
до определённой даты, выберите дату окончания периода''',
                         reply_markup=await calendar.start_calendar(year=2024, month=1))

@router.message(Request.request_type, F.text.lower() == "за определённый период")
async def get_period_stats(message: types.Message, state: FSMContext):
    await state.set_state(Request.start_date)
    calendar = SimpleCalendar(
        locale=await get_user_locale(message.from_user), show_alerts=True
    )
    calendar.set_dates_range(datetime.datetime(2024, 1, 1),
                             datetime.datetime.today())  # replace with portfolio creation
    await message.reply('''Для получения статистики за определённый период \
сначала введите год \(или выберите текущий\) и выберите месяц и число его начала, \
затем введите год и выберите месяц и число его окончания''',
                         reply_markup=await calendar.start_calendar(year=2024, month=1))

@router.callback_query(Request.start_date, SimpleCalendarCallback.filter())
async def get_start_date(callback_query: CallbackQuery, callback_data: CallbackData, state: FSMContext):
    calendar = SimpleCalendar(
        locale=await get_user_locale(callback_query.from_user), show_alerts=True
    )
    calendar.set_dates_range(datetime.datetime(2024, 1, 1), datetime.datetime.today())
    selected, date = await calendar.process_selection(callback_query, callback_data)
    if selected:
        await state.update_data(start_date=date)
        await state.set_state(Request.end_date)
        calendar = SimpleCalendar(
            locale=await get_user_locale(callback_query.from_user), show_alerts=True
        )
        calendar.set_dates_range(datetime.datetime(2024, 1, 1),
                                 datetime.datetime.today())  # replace with portfolio creation
        await callback_query.message.answer("Отлично\! Теперь выберите дату окончания",
                                            reply_markup=await calendar.start_calendar(year=2024, month=1))

@router.callback_query(Request.end_date, SimpleCalendarCallback.filter())
async def get_end_date(callback_query: CallbackQuery, callback_data: CallbackData, state: FSMContext):
    calendar = SimpleCalendar(
        locale=await get_user_locale(callback_query.from_user), show_alerts=True
    )
    calendar.set_dates_range(datetime.datetime(2024, 1, 1), datetime.datetime.today())
    selected, date = await calendar.process_selection(callback_query, callback_data)
    if selected:
        await state.update_data(end_date=date)
        data = await state.get_data()

        request = await form_request(data["security_type"], data["start_date"].date(), data["end_date"].date())
        request.token = token_encoder.decode_token(data["encoded_token"])

        request_time_str = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        request_file_name = f"request_shares_{hashlib.sha256((request.token + request_time_str).encode('utf-8')).hexdigest()}.json"
        request_path = "../../connector_requests/" + request_file_name

        async with async_open(request_path, 'wb') as f:
            await f.write(orjson.dumps(request))

        response_file_name = f"response_shares_{hashlib.sha256((request.token + request_time_str).encode('utf-8')).hexdigest()}.json"
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

        if Path(response_path).exists():
            Path(response_path).unlink()
        if not results:
            await callback_query.message.answer(
                "К сожалению, Ваш запрос не удалось обработать\. Попробуйте позже или скорректируйте запрос")
        else:
            result_msg = await form_result(results)
            await callback_query.message.answer(result_msg)
        await state.clear()