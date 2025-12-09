import os
import dotenv
import logging
import uuid
import json
from pathlib import Path  # <-- добавлено
from langchain_openai import ChatOpenAI
import re
import traceback

from src.agents.create_api_agent import create_api_agent
from src.agents.extraction_agent import create_extraction_agent
from src.agents.supervisor import create_supervisor
from src.agents.technical_task_agent import technical_task_agent_prompt, create_technical_task
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun
from langgraph.checkpoint.memory import InMemorySaver

dotenv.load_dotenv('doc_2025-11-22_13-44-09.env')
api_key = os.getenv("API_KEY_GPT")
if not api_key:
    raise ValueError("API_KEY_GPT не найден в .env файле")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(name)s] - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("PP.log", encoding="utf-8"),
    ],
)

client = ChatOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
    model="x-ai/grok-4.1-fast:free",  # <-- бесплатная модель
)

########
technical_task_agent = create_technical_task(model=client)

@tool
def call_technical_task_agent(request: str) -> str:
    """создает техническое задание по запросу пользователя"""
    result = technical_task_agent.invoke({
        "messages": [{"role": "user", "content": request}]
    })
    return result["messages"][-1].content
############

api_agent = create_api_agent(model=client)

@tool
def call_api_agent(request: str) -> str:
    """создает апи по запросу пользователя"""
    result = api_agent.invoke({
        "messages": [{"role": "user", "content": request}]
    })
    return result["messages"][-1].text
#########

parse_agent = create_agent(model=client)

@tool
def call_parse_agent(request: str) -> str:
    """подставляет данные пользователя"""
    result = parse_agent.invoke({
        "messages": [{"role": "user", "content": request}]
    })
    return result["messages"][-1].text
####################

# Инициализация extraction_agent
extraction_agent = create_extraction_agent(model=client)

# Вспомогательная функция для извлечения JSON (скопирована из вашего файла extraction_agent)
def extract_json_from_text(text: str):
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

@tool
def call_extraction_agent(request: str) -> str:
    """Извлекает структурированные данные из указанного файла по описанию пользователя."""
    try:
        # request — JSON-строка вида: {"file_path": "...", "fields_description": "извлеки номер счёта отправителя и телефон"}
        input_data = json.loads(request)
        file_path = input_data.get("file_path")
        fields_description = input_data.get("fields_description")

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

        user_prompt = f"Файл: {resolved_path}\n\nЗадача: {fields_description}"
        messages = [{"role": "user", "content": user_prompt}]
        result = extraction_agent.invoke({"messages": messages})
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
        return json.dumps({
            "error": f"Критическая ошибка: {str(e)}",
            "traceback": traceback.format_exc()
        }, ensure_ascii=False)

#####################

supervisor_tools = [call_technical_task_agent, call_api_agent, call_parse_agent, call_extraction_agent]

supervisor = create_supervisor(client, supervisor_tools)

if __name__ == "__main__":
    thread_id = uuid.uuid4()
    while True:
        user_input = input("\nПользователь: ")
        if user_input.lower() in {"выход", "exit", "quit"}:
            print("Диалог завершён.")
            break

        config = {
            "configurable": {
                "thread_id": thread_id
            }
        }

        for step in supervisor.stream(
                {"messages": [{"role": "user", "content": user_input}]},
                config=config
        ):
            for update in step.values():
                for message in update.get("messages", []):
                    message.pretty_print()