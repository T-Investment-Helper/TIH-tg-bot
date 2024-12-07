from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from source.Bot.messages import sign_in_msg, get_confirm_msg
from source.Encoder.encoder import token_encoder
from source.Router.db_interaction import add_new_user

router = Router()

class User(StatesGroup):
    id = State()
    token = State()
    confirmation = State()

@router.message(F.text.lower() == "войти")
async def sign_in(message: types.Message, state: FSMContext):
    await state.update_data(id=message.from_user.id)
    await state.set_state(User.token)
    await message.reply(sign_in_msg)

@router.message(User.token, F.text)
async def get_token(message: types.Message, state: FSMContext):
    token = message.text
    await state.update_data(token=token)
    await state.set_state(User.confirmation)
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="Подтвердить"))
    builder.add(types.KeyboardButton(text="Не подтверждать"))
    builder.adjust(2)
    await message.reply(f'''Подтвердите, пожалуйста, отправку токена, нажав кнопку "Подтвердить" \
или написав "Подтвердить" \(в любом регистре\)\.

Обратите внимание, что это последний шанс стереть введённый токен, написав /cancel\! После \
подтверждения зашифрованный токен будет внесён в базу данных, изменить его можно будет только \
войдя заново\.''',
                        reply_markup=builder.as_markup(resize_keyboard=True))

@router.message(User.confirmation, F.text)
async def get_confirmation(message: types.Message, state: FSMContext):
    if message.text.lower() == "подтвердить":
        data = await state.get_data()
        # encoded_token = token_encoder.encode_token(data["token"])
        encoded_token = data["token"]
        try:
            add_new_user(str(data["id"]), encoded_token)

            builder = ReplyKeyboardBuilder()
            builder.add(types.KeyboardButton(text="Помощь"))
            builder.add(types.KeyboardButton(text="Статистика"))
            await message.reply(get_confirm_msg,
                                reply_markup=builder.as_markup(resize_keyboard=True))
            await state.clear()
        except Exception:
            await message.reply("К сожалению, войти не удалось\. Попробуйте, пожалуйста, позже")
    else:
        builder = ReplyKeyboardBuilder()
        builder.add(types.KeyboardButton(text="Подтвердить"))
        builder.add(types.KeyboardButton(text="Не подтверждать"))
        builder.adjust(2)
        await message.reply(f'''Подтвердите, пожалуйста, отправку токена, нажав кнопку "Подтвердить" \
        или написав "Подтвердить" \(в любом регистре\), или сотрите его, написав /cancel''',
                            reply_markup=builder.as_markup(resize_keyboard=True))