# Библиотеки
import os
import dotenv
import logging
import uuid
import sys

from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain.tools import tool

# Интеграции
from src.agents.create_api_agent import create_api_agent
from src.agents.extraction_agent import create_extraction_agent
from src.agents.supervisor import create_supervisor
from src.agents.technical_task_agent import create_technical_task
from src.tools.execution_tools import run_python_code, save_script
from src.tools.data_extraction_tool import call_extraction_agent, set_extraction_agent

index_scripts = 1

# Настройка системы
dotenv.load_dotenv('.env')
api_key = os.getenv("API_KEY_GPT")
model_name = os.getenv("MODEL_NAME")

# Проверка наличия ключа API
if not api_key:
    raise ValueError("API_KEY_GPT не найден в .env файле")

# Подключение логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(name)s] - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("PP.log", encoding="utf-8"),
    ],
)

# Модель
client = ChatOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
    model=model_name
)

technical_task_agent = create_technical_task(model=client)

@tool
def call_technical_task_agent(request: str) -> str:
    """Создание технического задания по запросу пользователя"""
    result = technical_task_agent.invoke({
        "messages": [{"role": "user", "content": request}]
    })
    return result["messages"][-1].content

api_agent = create_api_agent(model=client)

@tool
def call_api_agent(request: str) -> str:
    """Создание API по запросу пользователя"""
    result = api_agent.invoke({
        "messages": [{"role": "user", "content": request}]
    })
    return result["messages"][-1].text

parse_agent_tools = [run_python_code, save_script]
parse_agent = create_agent(model=client, tools=parse_agent_tools)

@tool
def call_parse_agent(request: str) -> str:
    """подставляет данные пользователя"""
    result = parse_agent.invoke({
        "messages": [{"role": "user", "content": request}]
    })
    return result["messages"][-1].text

extraction_agent = create_extraction_agent(model=client)
set_extraction_agent(extraction_agent)

supervisor_tools = [
    call_technical_task_agent,
    call_api_agent,
    call_parse_agent,
    call_extraction_agent
]
supervisor = create_supervisor(client, supervisor_tools)

# Основной цикл
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
            },
        }

        for step in supervisor.stream(
                {"messages": [{"role": "user", "content": user_input}]},
                config=config
        ):
            for update in step.values():
                for message in update.get("messages", []):
                    message.pretty_print()