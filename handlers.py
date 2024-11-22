from aiogram import types, Router, F
from aiogram.filters import Command
from service import (
    send_question,
    new_quiz,
    update_quiz_state,
    get_correct_answers,
    end_quiz,
    get_current_question_data,
    get_quiz_index,
    get_total_questions,
)
import logging

router = Router()
logging.basicConfig(level=logging.INFO)


@router.callback_query(F.data == "right_answer")
async def right_answer(callback: types.CallbackQuery):
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("Верно!")

    user_id = callback.from_user.id
    await update_quiz_state(user_id, correct=True)

    total_questions = await get_total_questions()
    current_question_index = await get_quiz_index(user_id)

    if current_question_index >= total_questions:
        correct_answers = await get_correct_answers(user_id)
        await callback.message.answer(
            f"Квиз завершен! Вы набрали {correct_answers} правильных ответов из {total_questions}."
        )
        await end_quiz(user_id)
    else:
        has_question = await send_question(callback.message, user_id)
        if not has_question:
            correct_answers = await get_correct_answers(user_id)
            await callback.message.answer(
                f"Квиз завершен! Вы набрали {correct_answers} правильных ответов из {total_questions}."
            )
            await end_quiz(user_id)


@router.callback_query(F.data == "wrong_answer")
async def wrong_answer(callback: types.CallbackQuery):
    await callback.message.edit_reply_markup(reply_markup=None)
    user_id = callback.from_user.id
    question_data = await get_current_question_data(user_id)

    if question_data:
        correct_option_index = question_data["correct_option"]
        options = question_data["options"]
        correct_answer = options[correct_option_index]
        await callback.message.answer(f"Неправильно. Правильный ответ: {correct_answer}")
    else:
        await callback.message.answer("Произошла ошибка при получении данных вопроса.")
        return

    await update_quiz_state(user_id, correct=False)
    total_questions = await get_total_questions()
    current_question_index = await get_quiz_index(user_id)

    if current_question_index >= total_questions:
        correct_answers = await get_correct_answers(user_id)
        await callback.message.answer(
            f"Квиз завершен! Вы набрали {correct_answers} правильных ответов из {total_questions}."
        )
        await end_quiz(user_id)
    else:
        has_question = await send_question(callback.message, user_id)
        if not has_question:
            correct_answers = await get_correct_answers(user_id)
            await callback.message.answer(
                f"Квиз завершен! Вы набрали {correct_answers} правильных ответов из {total_questions}."
            )
            await end_quiz(user_id)


@router.message(F.text == "Начать игру")
async def start_game(message: types.Message):
    cover_image_url = 'https://storage.yandexcloud.net/quizbot-buc/DALL%C2%B7E%202024-11-19%2011.56.35%20-%20A%20vibrant%20and%20engaging%20cover%20image%20for%20a%20quiz%20bot,%20featuring%20a%20colorful%20gradient%20background%20with%20abstract%20geometric%20shapes.%20The%20center%20displays%20a%20glow.webp?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=YCAJEESPWF5Lzunkz4SdZ4M0A%2F20241119%2Fru-central1%2Fs3%2Faws4_request&X-Amz-Date=20241119T060453Z&X-Amz-Expires=2592000&X-Amz-Signature=E97D610FE7A74102CEF34D3AB7AADD3DF8AECB3AFEDA84FA6573DF731E68C5B7&X-Amz-SignedHeaders=host'

    await message.answer_photo(photo=cover_image_url, caption="Добро пожаловать в квиз!")
    await new_quiz(message)


@router.message(Command("quiz"))
async def cmd_quiz(message: types.Message):
    cover_image_url = 'https://storage.yandexcloud.net/quizbot-buc/DALL%C2%B7E%202024-11-19%2011.56.35%20-%20A%20vibrant%20and%20engaging%20cover%20image%20for%20a%20quiz%20bot,%20featuring%20a%20colorful%20gradient%20background%20with%20abstract%20geometric%20shapes.%20The%20center%20displays%20a%20glow.webp?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=YCAJEESPWF5Lzunkz4SdZ4M0A%2F20241119%2Fru-central1%2Fs3%2Faws4_request&X-Amz-Date=20241119T060453Z&X-Amz-Expires=2592000&X-Amz-Signature=E97D610FE7A74102CEF34D3AB7AADD3DF8AECB3AFEDA84FA6573DF731E68C5B7&X-Amz-SignedHeaders=host'

    await message.answer_photo(photo=cover_image_url, caption="Добро пожаловать в квиз!")
    await message.answer("Давайте начнем квиз!")
    await new_quiz(message)