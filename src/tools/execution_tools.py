# Библиотеки
import os
import subprocess
import sys
import logging

from langchain.tools import tool

# Логи
logger = logging.getLogger(__name__)

"""
Перенесенные функции из main.py в отдельный файл.
Данный файл предназначен для инструментов выполнения.
"""

@tool
def run_python_code(filename: str) -> str:
    """
    Запускает Python-файл через subprocess, возвращает результат и удаляет файл после выполнения
    Args:
        filename (str): Имя файла для запуска.
    Returns:
        str: Вывод выполнения или сообщение об ошибке.
    """
    try:
        # Проверка на существование файла
        if not os.path.exists(filename):
            logger.error(f"Файл не найден: {filename}")
            return "Файл не найден"

        # Запускаем файл через python (или python3)
        result = subprocess.run(
            [sys.executable, filename],  # sys.executable - текущий интерпретатор
            capture_output=True,  # захватываем stdout и stderr
            text=True,  # возвращаем строки, а не байты
            timeout=30,  # таймаут 30 секунд
        )

        # Сохраняем результат перед удалением
        output = result.stdout

        # Логируем ошибки если есть
        if result.stderr:
            logger.error(f"STDERR при выполнении {filename}: {result.stderr}")
        logger.info(f"Return code при выполнении {filename}: {result.returncode}")

        # Удаляем файл после выполнения
        try:
            if os.path.exists(filename):
                os.remove(filename)
                logger.info(f'Файл удалён: {filename}')
        except Exception as e:
            logger.error(f"Не удалось удалить файл {filename}: {e}")
        return output

    except subprocess.TimeoutExpired:
        logger.error(f"Timeout: {filename} не завершился за 30 секунд")
        # Попытка удалить файл даже при таймауте
        try:
            if os.path.exists(filename):
                os.remove(filename)
        except Exception as e:
            logger.error(f'Не удалось удалить файл {filename} после таймаута: {e}')
        return "Timeout error"

    except FileNotFoundError:
        logger.error(f"Файл не найден: {filename}")
        return "File not found"

    except Exception as e:
        logger.error(f"Ошибка при выполнении {filename}: {e}")
        # Попытка удалить файл даже при ошибке
        try:
            if os.path.exists(filename):
                os.remove(filename)
        except Exception as remove_e:
            logger.error(f"Не удалось удалить файл {filename} после ошибки: {remove_e}")
        return f"Error: {str(e)}"

@tool
def save_script(code: str, filename: str = 'temp_script') -> str:
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
        if not filename.endswith('.py'):
            filename += '.py'
        script_dir = "scripts"
        full_path = os.path.join(script_dir, filename)

        # Сохраняем код в файл
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(code)
        logger.info(f"Файл сохранён: {full_path}")
        return str(full_path)
    except PermissionError:
        error_msg = f"❌ Ошибка: Нет прав на запись в {script_dir}"
        logger.error(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"Ошибка сохранения: {str(e)}"
        logger.error(error_msg)
        return error_msg