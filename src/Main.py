import os
import dotenv
import logging
import uuid
import json
from pathlib import Path
from langchain_openai import ChatOpenAI
import traceback

from src.agents.create_api_agent import create_api_agent
from src.agents.extraction_agent import create_extraction_agent
from src.agents.supervisor import create_supervisor
from src.agents.technical_task_agent import create_technical_task
from langchain.agents import create_agent
from langchain.tools import tool
import re
import subprocess
import sys
from typing import Optional

index_scripts = 1

dotenv.load_dotenv('.env')
api_key = os.getenv("API_KEY_GPT")
model_name = os.getenv("MODEL_NAME")
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
    model=model_name# <-- бесплатная модель
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
@tool
def run_python_code(filename: str) -> str:
    """Запускает Python-файл через subprocess, возвращает результат и удаляет файл после выполнения"""
    try:
        # Запускаем файл через python (или python3)
        result = subprocess.run(
            [sys.executable, filename],  # sys.executable - текущий интерпретатор
            capture_output=True,  # захватываем stdout и stderr
            text=True,  # возвращаем строки, а не байты
            timeout=30,  # таймаут 30 секунд
        )

        # Сохраняем результат перед удалением
        output = result.stdout

        # Выводим информацию об ошибках если есть
        if result.stderr:
            print("STDERR:", result.stderr)
        print(f"Return code: {result.returncode}")

        # Удаляем файл после выполнения
        try:
            if os.path.exists(filename):
                os.remove(filename)
                print(f"Файл удалён: {filename}")
        except Exception as e:
            print(f"Не удалось удалить файл {filename}: {e}")

        return output

    except subprocess.TimeoutExpired:
        print(f"Timeout: {filename} не завершился за 30 секунд")
        # Попытка удалить файл даже при таймауте
        try:
            if os.path.exists(filename):
                os.remove(filename)
        except:
            pass
        return "Timeout error"
    except FileNotFoundError:
        print(f"Файл не найден: {filename}")
        return "File not found"
    except Exception as e:
        print(f"Ошибка: {e}")
        # Попытка удалить файл даже при ошибке
        try:
            if os.path.exists(filename):
                os.remove(filename)
        except:
            pass
        return f"Error: {str(e)}"


@tool
def save_script(code: str, filename: Optional[str] = None) -> str:
    """
    Сохраняет Python код (строку) в файл .py.

    Args:
        code (str): Python код для сохранения
        filename (str, optional): Имя файла. По умолчанию "temp_script.py"

    Returns:
        str: Путь к сохраненному файлу или сообщение об ошибке
    """
    try:
        # Формируем имя файла
        if filename is None:
            filename = "temp_script.py"
        elif not filename.endswith('.py'):
            filename += '.py'

        script_dir = "scripts"
        full_path = os.path.join(script_dir, filename)
        # Сохраняем код в файл
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(code)
        return full_path

    except PermissionError:
        return f"❌ Ошибка: Нет прав на запись в {script_dir}"
    except Exception as e:
        return f"❌ Ошибка сохранения: {str(e)}"

parse_agent_tools = [run_python_code, save_script]
parse_agent = create_agent(model=client, tools=parse_agent_tools)

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

def extract_json_from_text(text: str) -> dict[str, any]:
    """Пытается извлечь JSON из текста (включая случаи с обёрткой в ```json ... ``` или лишними словами)."""
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
    except (json.JSONDecodeError, ValueError):
        # Если не удалось распарсить — возвращаем пустой словарь
        return {}

@tool
def call_extraction_agent(file_path: str, fields_description: str) -> str:
    """Извлекает структурированные данные из указанного файла по описанию пользователя."""
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
            },
        }

        for step in supervisor.stream(
                {"messages": [{"role": "user", "content": user_input}]},
                config=config
        ):
            for update in step.values():
                for message in update.get("messages", []):
                    message.pretty_print()