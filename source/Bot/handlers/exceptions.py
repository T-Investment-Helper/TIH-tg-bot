from aiogram import Router, types

router = Router()

@router.message()
async def unsupported_message(message: types.Message):
    await message.answer("Ваше сообщение застало нас врасплох, пожалуйста, \
отправьте поддерживаемую команду или напишите /help")