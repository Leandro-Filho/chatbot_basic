from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch
from langchain_core.messages import ToolMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.types import Command, interrupt
from dotenv import load_dotenv
load_dotenv()   

#aqui, a função desse dicionario é: com o typeddict, colocar valores nos atributos que serão colocaddos em state e a variavel message terá um acumulo de mensagens sem nenhuma sobreescrever por conta da função add_messages.
class State(TypedDict):
    messages: Annotated[list, add_messages] #aqui é resposaável por criar as mensagens e não deixar que sejam sobrepostas umas nas outras

graph_builder = StateGraph(State)

def human_assistance(query: str) -> str:
    """Request assistance from a human."""
    human_response = interrupt({"query": query})
    return human_response["data"]

#aqui é feito a "criação" de uma llm dentro do nosso código usando uma modleo de linguagem da OpenAI, mais especificamente o modelo "gpt-4o-mini".
llm = ChatOpenAI(model_name="gpt-4o-mini")

#cria em variável com o tavily search, resposável por buscar em apenas 2 urls sobre os assunto colocado no input
tool = TavilySearch(max_results=2)

#aqui, apenas criamos uma lista de ferramentas, já que na classe abaixo, ele espera como resposta uma lista 
tools = [tool, human_assistance]

#aqui, definimos que a llm da openai vai usar os tools de busca em urls
llm_with_tools = llm.bind_tools(tools)


def chatbot(state: State):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

#aqui terá como função principal construir as arestas entre os nós, ou seja, interligando cada ação/nó criados
graph_builder.add_node("chatbot", chatbot)

tool_node = ToolNode(tools=tools)
graph_builder.add_node("tools", tool_node)
graph_builder.add_conditional_edges(
    "chatbot",
    tools_condition,
)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)

#aqui, é onde a memória é adicionada ao grafo, ou seja, é onde o grafo irá salvar as mensagens e estados do chatboot
memory = InMemorySaver()
graph = graph_builder.compile(checkpointer=memory)

# aqui, o config tem como função de colocar um id na conversa, fazendo com que ela seja guardada
config = {"configurable": {"thread_id": "1"}}

#aqui, é a função com um loop que fará o chat conversar com nós 

# Define uma função chamada 'stream_graph_updates' que recebe a entrada do usuário como string
def stream_graph_updates(user_input: str):
    # Itera sobre cada evento retornado pelo método 'stream' do objeto 'graph'. Esse método recebe como entrada um dicionário com mensagens, onde a primeira mensagem é do "user" com o conteúdo vindo de 'user_input'
    for event in graph.stream({"messages": [{"role": "user", "content": user_input}]}):
        
        # Para cada evento, percorre todos os valores retornados (cada valor pode conter várias saídas)
        for value in event.values():
            # Imprime no console a última mensagem gerada pelo assistente no fluxo 'messages' é uma lista, e '[-1]' pega a mais recente
            print("Assistant:", value["messages"][-1].content)

# Loop infinito para interagir continuamente com o usuário
while True:
    try:

        # Pede a entrada do usuário no console
        user_input = input("User: ")

        # Se o usuário digitar 'quit', 'exit' ou 'q', encerra o loop
        if user_input.lower() in ["quit", "exit", "q", "tchau", "adeus", "bye", "obrigado pela ajuda"]:
            print("Tchau! Até a próxima!")
            break
        
        # Caso contrário, chama a função para processar a entrada e responder
        stream_graph_updates(user_input)

    except:
            user_input = "I need some expert guidance for building an AI agent. Could you request assistance for me?"
            config = {"configurable": {"thread_id": "1"}}

    events = graph.stream(
        {"messages": [{"role": "user", "content": user_input}]},
        config,
        stream_mode="values",
    )
    for event in events:
        event["messages"][-1].pretty_print()
    
    human_response = (
    "We, the experts are here to help! We'd recommend you check out LangGraph to build your agent."
    " It's much more reliable and extensible than simple autonomous agents."
    )

    human_command = Command(resume={"data": human_response})

    events = graph.stream(human_command, config, stream_mode="values")
    for event in events:
        if "messages" in event:
            event["messages"][-1].pretty_print()