from database import pool, execute_update_query, execute_select_query
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import types
import logging

logging.basicConfig(level=logging.INFO)

# Функция для генерации клавиатуры с вариантами ответа
def generate_options_keyboard(answer_options, right_answer):
    builder = InlineKeyboardBuilder()

    for option in answer_options:
        builder.add(
            types.InlineKeyboardButton(
                text=option,
                callback_data="right_answer" if option == right_answer else "wrong_answer",
            )
        )

    builder.adjust(1)
    return builder.as_markup()

# Функция для получения общего количества вопросов
async def get_total_questions():
    query = "SELECT COUNT(*) as total FROM `quiz_data`;"
    try:
        result = await execute_select_query(pool, query)
        return int(result[0]['total']) if result and 'total' in result[0] else 0
    except Exception as e:
        logging.error(f"Ошибка при получении общего количества вопросов: {e}")
        return 0

# Функция для получения текущих данных вопроса
async def get_current_question_data(user_id):
    current_question_index = await get_quiz_index(user_id)
    total_questions = await get_total_questions()

    if current_question_index >= total_questions:
        logging.info(f"Индекс {current_question_index} превышает количество вопросов ({total_questions}).")
        return None

    query = """
    DECLARE $offset AS Uint64;
    SELECT question_id, question, options, correct_option 
    FROM `quiz_data` 
    ORDER BY question_id
    LIMIT 1
    OFFSET $offset;
    """
    try:
        result = await execute_select_query(pool, query, offset=current_question_index)
        if result:
            row = result[0]
            return {
                "id": row["question_id"],
                "question": row["question"],
                "options": row["options"].split(",") if isinstance(row["options"], str) else [],
                "correct_option": int(row["correct_option"]),
            }
        return None
    except Exception as e:
        logging.error(f"Ошибка при получении данных текущего вопроса: {e}")
        return None

# Функция для отправки вопроса пользователю
async def send_question(message, user_id):
    question_data = await get_current_question_data(user_id)
    if not question_data:
        logging.warning("Вопросы закончились или данные отсутствуют.")
        return False

    try:
        correct_option_index = question_data['correct_option']
        options = question_data['options']

        if not isinstance(options, list) or correct_option_index >= len(options):
            raise ValueError("Неправильный формат данных вопроса или индекс ответа.")

        right_answer = options[correct_option_index]
        kb = generate_options_keyboard(options, right_answer)
        await message.answer(f"{question_data['question']}", reply_markup=kb)
        return True
    except Exception as e:
        logging.error(f"Ошибка при отправке вопроса: {e}")
        await message.answer("Произошла ошибка при подготовке вопроса.")
        return False

# Функция для обновления состояния квиза
async def update_quiz_state(user_id, correct):
    current_question_index = await get_quiz_index(user_id)
    next_question_index = current_question_index + 1
    total_questions = await get_total_questions()

    query_index = """
    DECLARE $user_id AS Uint64;
    DECLARE $question_index AS Uint64;
    UPSERT INTO `quiz_state` (user_id, question_index)
    VALUES ($user_id, $question_index);
    """
    await execute_update_query(pool, query_index, user_id=user_id, question_index=min(next_question_index, total_questions))

    if correct:
        query_score = """
        DECLARE $user_id AS Uint64;
        UPDATE `quiz_results`
        SET correct_answers = correct_answers + 1
        WHERE user_id = $user_id;
        """
        await execute_update_query(pool, query_score, user_id=user_id)

# Функция для получения индекса текущего вопроса
async def get_quiz_index(user_id):
    query = """
    DECLARE $user_id AS Uint64;
    SELECT question_index
    FROM `quiz_state`
    WHERE user_id == $user_id;
    """
    try:
        results = await execute_select_query(pool, query, user_id=user_id)
        return int(results[0]["question_index"]) if results else 0
    except Exception as e:
        logging.error(f"Ошибка при получении индекса текущего вопроса: {e}")
        return 0

# Функция для получения количества правильных ответов
async def get_correct_answers(user_id):
    query = """
    DECLARE $user_id AS Uint64;
    SELECT correct_answers
    FROM `quiz_results`
    WHERE user_id == $user_id;
    """
    try:
        results = await execute_select_query(pool, query, user_id=user_id)
        return int(results[0]["correct_answers"]) if results else 0
    except Exception as e:
        logging.error(f"Ошибка при получении количества правильных ответов: {e}")
        return 0

# Функция для начала нового квиза
async def start_quiz(user_id):
    query_index = """
    DECLARE $user_id AS Uint64;
    UPSERT INTO `quiz_state` (user_id, question_index)
    VALUES ($user_id, 0);
    """
    await execute_update_query(pool, query_index, user_id=user_id)

    query_score = """
    DECLARE $user_id AS Uint64;
    UPSERT INTO `quiz_results` (user_id, correct_answers)
    VALUES ($user_id, 0);
    """
    await execute_update_query(pool, query_score, user_id=user_id)

# Функция для начала нового квиза и отправки первого вопроса
async def new_quiz(message):
    user_id = message.from_user.id
    await start_quiz(user_id)
    has_question = await send_question(message, user_id)
    if not has_question:
        await message.answer("Вопросы для квиза не найдены.")

# Функция для завершения квиза
async def end_quiz(user_id):
    query_reset = """
    DECLARE $user_id AS Uint64;
    UPDATE `quiz_state`
    SET question_index = 0
    WHERE user_id = $user_id;
    """
    await execute_update_query(pool, query_reset, user_id=user_id)
