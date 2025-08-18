from typing import TypedDict, Annotated
from langchain_openai import ChatOpenAI
from langchain_core.messages import AnyMessage
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import ToolNode
from langchain_tavily import TavilySearch
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
load_dotenv()

# Definição do estado do chatbot
class State(TypedDict):
    messages: Annotated[list, add_messages]  # Corrigido: precisa ser lista, não str

# Modelo da OpenAI
model = ChatOpenAI(model="gpt-4o-mini")

# Ferramenta de busca Tavily
tool = TavilySearch(max_results=2)
tools = [tool]

# Bindando as ferramentas ao modelo
model = model.bind_tools(tools)

# Nó que chama o LLM
def chatbot(state: State):
    return {"messages": [model.invoke(state["messages"])]}

# Criando o grafo do fluxo
graph_builder = StateGraph(State)
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("tools", ToolNode(tools))  # Usando ToolNode pronto do LangGraph

# Definindo as arestas do grafo
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("tools", "chatbot")
graph_builder.add_edge("chatbot", END)

# Memória do chatbot
memory = InMemorySaver()
graph = graph_builder.compile(checkpointer=memory)

# Configuração para manter o histórico de conversas
config = {"configurable": {"thread_id": "1"}}

# Loop principal do chatbot
while True:
    user_input = input("Você: ")
    if user_input.lower() in ["sair", "exit", "quit"]:
        print("Chat encerrado.")
        break

    # Stream de respostas do grafo com memória
    for event in graph.stream({"messages": [{"role": "user", "content": user_input}]}, config=config):
        for value in event.values():
            if "messages" in value:
                print("🤖:", value["messages"][-1].content)
