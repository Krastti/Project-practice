import os
import json
from pathlib import Path
from typing import Dict, Any
import re

from langchain_community.document_loaders import TextLoader, PyPDFLoader, UnstructuredWordDocumentLoader, CSVLoader
from langchain.agents import create_agent
from langchain.tools import tool


extraction_agent_prompt = """
Ты — агент для извлечения структурированных данных из документов. Пользователь передаёт тебе путь к файлу и описание того, какие данные нужно извлечь (например: "номер счёта отправителя", "дата платежа", "сумма", "телефон").

Ты можешь использовать инструмент `retrieve_document_content`, чтобы загрузить текст документа.

После анализа текста верни ТОЛЬКО валидный JSON с запрошенными полями. Если какое-то поле не найдено в документе — укажи для него значение `null`.

Пример ожидаемого вывода:
{
  "sender_account": "40817810123456789012",
  "sender_phone": "+79123456789",
  "amount": 15000.0,
  "date": "2024-05-15"
}

Не добавляй пояснений, markdown, обёрток вроде ```json. Верни строго JSON.
"""


@tool
def retrieve_document_content(file_path: str) -> str:
    """Загружает содержимое документа по указанному пути и возвращает его как текст."""
    try:
        file_path = str(Path(file_path).resolve())
        if not os.path.exists(file_path):
            return f"Ошибка: файл не найден: {file_path}"
        if not os.access(file_path, os.R_OK):
            return f"Ошибка: нет прав на чтение файла: {file_path}"

        ext = Path(file_path).suffix.lower()
        loaders = {
            '.txt': TextLoader,
            '.pdf': PyPDFLoader,
            '.docx': UnstructuredWordDocumentLoader,
            '.csv': CSVLoader
        }
        if ext not in loaders:
            return f"Ошибка: неподдерживаемый формат: {ext}"

        if ext == '.txt':
            try:
                loader = TextLoader(file_path, encoding='utf-8')
                docs = loader.load()
            except UnicodeDecodeError:
                loader = TextLoader(file_path, encoding='cp1251')
                docs = loader.load()
        else:
            loader = loaders[ext](file_path)
            docs = loader.load()

        full_text = "\n\n".join([doc.page_content for doc in docs])
        return full_text[:50000]
    except Exception as e:
        return f"Ошибка при загрузке файла: {str(e)}"


@tool
def extract_json_from_text(text: str):
    """Вспомогательная функция для извлечения JSON"""
    try:
        text = re.sub(r"```(?:json)?", "", text).strip()
        start = text.find("{")
        end = text.rfind("}") + 1
        if start == -1 or end == 0:
            raise ValueError("No JSON-like structure found")
        json_str = text[start:end]
        return json.loads(json_str)
    except (json.JSONDecodeError, ValueError):
        return {}


# Создание инструментов (функций, помеченных @tool, которые принимают на вход str и возвращают str)
def create_extraction_agent(model):
    tools = [retrieve_document_content, extract_json_from_text]
    extraction_agent = create_agent(
        model=model,
        tools=tools,
        system_prompt=extraction_agent_prompt
    )
    return extraction_agent