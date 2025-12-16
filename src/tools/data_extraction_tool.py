# Библиотеки и импорты
import json
import re
import os
import traceback
import logging

from pathlib import Path
from langchain.tools import tool

"""
Перенесенные функции из main.py в отдельный файл.
Данный файл предназначен для инструментов извлечения.
"""

# Логи
logger = logging.getLogger(__name__)

# Инициализация extraction_agent
extraction_agent_instance = None

def set_extraction_agent(agent):
    """
    Функция для установки экземлпяра извне.
    Вызывается из main.py после инициализации модели.
    """
    global extraction_agent_instance
    extraction_agent_instance = agent

def extract_json_from_text(text: str) -> dict[str, any]:
    """
    Пытается извлечь JSON из текста (включая случаи с обёрткой в ```json ... ``` или лишними словами).
    """
    try:
        # Удаляем markdown-обёртку
        text = re.sub(r"```(?:json)?", "", text).strip()

        # Ищем начало и конец JSON
        start = text.find("{")
        end = text.rfind("}") + 1
        if start == -1 or end == 0:
            raise ValueError("No JSON-like structure found")

        json_str = text[start:end]
        return json.loads(json_str)

    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"Не удалось распарсить JSON из текста: {e}")
        # Если не удалось распарсить — возвращаем пустой словарь
        return {}


@tool
def call_extraction_agent(file_path: str, fields_description: str) -> str:
    """
    Извлекает структурированные данные из указанного файла по описанию пользователя.
    Args:
        file_path (str): Путь к файлу.
        fields_description (str): Описание полей для извлечения.
    Returns:
        str: JSON-строка с извлечёнными данными или ошибкой
    """
    try:
        if not file_path or not fields_description:
            return json.dumps({
                "error": "Отсутствует file_path или fields_description"
            }, ensure_ascii=False)

        resolved_path = str(Path(file_path).resolve())
        if not os.path.exists(resolved_path):
            return json.dumps({
                "error": f"Файл не найден: {resolved_path}"
            }, ensure_ascii=False)

        if not os.access(resolved_path, os.R_OK):
            return json.dumps({
                "error": f"Нет прав на чтение файла: {resolved_path}"
            }, ensure_ascii=False)

        user_prompt = f"""
        Ты — агент для извлечения данных. Верни ТОЛЬКО JSON с запрошенными полями.
        Файл: {resolved_path}
        Задача: {fields_description}
        """
        messages = [{"role": "user", "content": user_prompt}]

        result = extraction_agent_instance.invoke({"messages": messages})
        last_message = result["messages"][-1]
        raw_output = last_message.content if hasattr(last_message, 'content') else str(last_message)

        # Пытаемся извлечь JSON
        parsed = extract_json_from_text(raw_output)

        # Если парсинг не удался — возвращаем ошибку
        if not isinstance(parsed, dict):
            return json.dumps({
                "error": "Модель не вернула валидный JSON",
                "raw_output": raw_output
            }, ensure_ascii=False)

        # Убеждаемся, что результат — JSON-объект (не массив и не скаляр)
        if not parsed:
            return json.dumps({
                "error": "Пустой или недействительный ответ от модели",
                "raw_output": raw_output
            }, ensure_ascii=False)

        return json.dumps(parsed, ensure_ascii=False)

    except Exception as e:
        logger.error(f"Критическая ошибка в call_extraction_agent: {e}\n{traceback.format_exc()}")
        return json.dumps({
            "error": f"Критическая ошибка: {str(e)}",
            "traceback": traceback.format_exc()
        }, ensure_ascii=False)