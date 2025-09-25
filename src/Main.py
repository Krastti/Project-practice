
from dotenv import load_dotenv
import os
from langchain_gigachat.chat_models import GigaChat
from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor
from langchain_perplexity import ChatPerplexity

##инициализация
load_dotenv()

llm_giga = GigaChat(
    credentials=os.getenv("GIGA_CREDENTIALS"),
    verify_ssl_certs=False,
)
llm_perplexity = ChatPerplexity(temperature=0, pplx_api_key=os.getenv("PPLX_API_KEY"), model="sonar")

supervisor_prompt = (
    "Ты — супервизор-агент."
    "Твоя роль: управлять исполнением задач, полученных от пользователя. Сам ты никаких задач не решаешь и никакую работу не выполняешь." 
    "Алгоритм работы:"  
    "1. Получи задачу от пользователя."  
    "2. Определи, какие подзадачи нужно выполнить:"  
    "    - Если задача связана с формулировкой требований, созданием ТЗ или детализацией запроса пользователя → передай её агенту technical_task_agent." 
    "- Если задача связана с кодом, API или необходимостью оформить документацию по данному коду → передай её агенту create_api_agent.  "
    "3. Тебе нужно только распределять задачи и пересылать их соответствующему агенту."  
    "4. Если задача включает обе области сразу, разбей её на 2 подзадачи и направь каждую в нужного агента."  
    "5. Всегда возвращай пользователю агрегированный результат работы агентов в структурированном виде."
    "Запомни:"  
    "- Ты не выполняешь работу сам."  
    "- Ты отвечаешь только за маршрутизацию и декомпозицию задач.")

api_prompt = ()


create_technical_tusk_agent = create_react_agent(
    model=llm_giga,
    tools=[],
    prompt="Ты агент по созданию точных и четких технических тз по запросу пользователя",
    name="technical_tusk_agent"
)

create_api_agent = create_react_agent(
    model=llm_giga,
    tools=[],
    prompt="""Проанализируй предоставленный код API-метода и создай техническую документацию по следующей структуре.
Структура документации:

1. Описание метода
    Кратко опиши, что делает метод.

2. HTTP-метод и URL
    Укажи поддерживаемые HTTP-методы (GET/POST) и полный URL вызова.

3. Параметры запроса
    Оформи параметры в виде словаря, где ключ — имя параметра, а значение — словарь с полями: тип, обязательность, описание, пример значения.


Пример:
{
"user_id": {
"type": "int",
"required": true,
"description": "Идентификатор пользователя",
"example": 123456
},
"fields": {
"type": "string",
"required": false,
"description": "Список полей через запятую",
"example": "first_name,last_name"
},
"access_token": {
"type": "string",
"required": true,
"description": "Ключ доступа API",
"example": "abcdef123456"
},
"v": {
"type": "string",
"required": true,
"description": "Версия API",
"example": "5.199"
}
}

4. Пример запроса
    Покажи пример запроса (GET или POST) с подстановкой реальных параметров.

5. Структура ответа
    Опиши формат JSON-ответа, подробно объяснив поля.

6. Пример ответа
    Приведи полный пример JSON-ответа.

7. Ошибки
    Опиши возможные коды ошибок в виде словаря:


Пример:
{
"5": {
"description": "User not found"
},
"10": {
"description": "Missing access token"
}
}

8. Замечания
    Отметь особенности и рекомендации при использовании метода, если таковые есть.


---

Пример результата на основе Python-кода:

def get_user_info(user_id: int, fields: list, access_token: str) -> dict:
'''Получает данные пользователя по его ID'''
url = "[https://api.example.com/users.get](https://api.example.com/users.get)"
params = {'user_id': user_id, 'fields': ','.join(fields), 'access_token': access_token, 'v': '1.0'}
response = requests.get(url, params=params)
return response.json()

Ожидаемый текст документации:

get_user_info

Описание метода
Получает данные пользователя по идентификатору.

HTTP-метод и URL
GET [https://api.example.com/users.get](https://api.example.com/users.get)

Параметры запроса
{
"user_id": {
"type": "int",
"required": true,
"description": "Идентификатор пользователя",
"example": 123456
},
"fields": {
"type": "string",
"required": false,
"description": "Список полей через запятую",
"example": "first_name,last_name"
},
"access_token": {
"type": "string",
"required": true,
"description": "Ключ доступа API",
"example": "..."
},
"v": {
"type": "string",
"required": true,
"description": "Версия API",
"example": "1.0"
}
}

Пример запроса
GET [https://api.example.com/users.get?user_id=123456&fields=first_name,last_name&access_token=...&v=1.0](https://api.example.com/users.get?user_id=123456&fields=first_name,last_name&access_token=...&v=1.0)

Структура ответа
Ответ содержит объект "response", который является списком объектов пользователей. Каждый объект содержит:

- id (int) — идентификатор пользователя

- first_name (string) — имя пользователя

- last_name (string) — фамилия пользователя


Пример ответа
{
"response": [
{
"id": 123456,
"first_name": "Иван",
"last_name": "Петров"
}
]
}

Ошибки
{
"5": {
"description": "User not found"
},
"10": {
"description": "Missing access token"
}
}

Замечания
Для передачи больших данных используйте POST с заголовком multipart/form-data. Возвращаемые поля зависят от параметра fields.",
    name="api_agent""",
    name="crete_api_agent"
)


supervisor = create_supervisor(
    agents=[create_technical_tusk_agent, create_api_agent],
    model=llm_giga,
    prompt=supervisor_prompt
)

app = supervisor.compile()

res = app.invoke(
    {
        "messages" : [
            {
                "role" : "user",
                "content" : input()
            }
        ]
    }
)
for message in res["messages"]:
    print(message.pretty_print())
    print()

