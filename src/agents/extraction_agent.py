import os
from pathlib import Path

from langchain_community.document_loaders import TextLoader, PDFPlumberLoader, UnstructuredWordDocumentLoader, CSVLoader
from langchain_core.tools import tool
from langchain.agents import create_agent

extraction_agent_prompt = """
Ты — агент для извлечения структурированных данных из документов. Пользователь передаёт тебе путь к файлу и описание того, какие данные нужно извлечь (например: "номер счёта отправителя", "дата платежа", "сумма", "телефон", "имя собаки").

Ты можешь использовать инструмент `retrieve_document_content`, чтобы загрузить текст документа.

После анализа текста верни ТОЛЬКО валидный JSON с запрошенными полями. Если какое-то поле не найдено в документе — укажи для него значение `null`.

Пример ожидаемого вывода:
{
  "dog_name": "Адель",
  "sender_account": "40817810123456789012",
  "sender_phone": "+79123456789",
  "amount": 15000.0,
  "date": "2024-05-15"
}

Формат:
- Ты ДОЛЖЕН вернуть ТОЛЬКО JSON-объект.
- Никаких пояснений, никаких других слов, никаких markdown-обёрток (типа ```json).
- Только JSON.

Если ты не можешь извлечь нужные поля, всё равно верни JSON, но с `null` вместо значений.
"""

@tool
def retrieve_document_content(file_path: str) -> str:
    """Загружает содержимое документа по указанному пути и возвращает его как текст."""
    try:
        file_path = str(Path(file_path).resolve())
        print(f"[DEBUG] Пытаемся загрузить файл: {file_path}")  # <-- добавьте это
        if not os.path.exists(file_path):
            return f"Ошибка: файл не найден: {file_path}"
        if not os.access(file_path, os.R_OK):
            return f"Ошибка: нет прав на чтение файла: {file_path}"

        ext = Path(file_path).suffix.lower()
        loaders = {
            '.txt': TextLoader,
            '.pdf': PDFPlumberLoader,  # <-- замените на PDFPlumberLoader
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
        print(f"[DEBUG] Загруженный текст (первые 500 символов):\n{full_text[:500]}")
        return full_text[:50000]
    except Exception as e:
        print(f"[DEBUG] Ошибка при загрузке файла: {str(e)}")
        return f"Ошибка при загрузке файла: {str(e)}"

# Создание инструментов (функций, помеченных @tool, которые принимают на вход str и возвращают str)
def create_extraction_agent(model):
    tools = [retrieve_document_content]
    extraction_agent = create_agent(
        model=model,
        tools=tools,
        system_prompt=extraction_agent_prompt
    )
    return extraction_agent