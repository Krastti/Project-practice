
from dotenv import load_dotenv
import os
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_gigachat.chat_models import GigaChat
from langgraph.graph import StateGraph, START, END

from src.ChatState import ChatState

##инициализация
load_dotenv()

llm = GigaChat(
    credentials=os.getenv("GIGA_CREDENTIALS"),
    verify_ssl_certs=False,
)


def gen_png_graph(app_obj, name_photo: str = "graph.png") -> None:
    """
    Генерирует PNG-изображение графа и сохраняет его в файл.

    Args:
        app_obj: Скомпилированный объект графа
        name_photo: Имя файла для сохранения (по умолчанию "graph.png")
    """
    with open(name_photo, "wb") as f:
        f.write(app_obj.get_graph().draw_mermaid_png())

##узлы графа
def user_input_node(state: ChatState) -> dict:
    user_input = input("Вы: ")

    new_messages = state["messages"] + [HumanMessage(content=user_input)]
    return {"messages": new_messages}

def llm_create_technical_specifications_node(state: ChatState) -> dict:
    response = llm.invoke(state["messages"])
    content = response.content

    print(f"ИИ: {content}")

    new_messages = state["messages"] + [AIMessage(content=content)]
    return {"messages": new_messages}





##инициализация графа
initial_state = {
    "messages": [
        SystemMessage(
            content="Ты эксперт по составлению Техничских заданий.Твоя задача составлять ТЗ по данным пользователя"
        )
    ]
}
graph = StateGraph(ChatState)

graph.add_node("user_input", user_input_node)
graph.add_node("llm_create_technical_specifications", llm_create_technical_specifications_node)

graph.add_edge(START, "user_input")
graph.add_edge("user_input", "llm_create_technical_specifications")
graph.add_edge("llm_create_technical_specifications", END)

app = graph.compile()
app.invoke(initial_state)


