from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch
from langchain_core.messages import ToolMessage
from langgraph.checkpoint.memory import InMemorySaver
from dotenv import load_dotenv
load_dotenv()
import json

#aqui, a função desse dicionario é: com o typeddict, colocar valores nos atributos que serão colocaddos em state e a variavel message terá um acumulo de mensagens sem nenhuma sobreescrever por conta da função add_messages.
class State(TypedDict):
    messages: Annotated[list, add_messages] #aqui é resposaável por criar as mensagens e não deixar que sejam sobrepostas umas nas outras

graph_builder = StateGraph(State)

#aqui é feito a "criação" de uma llm dentro do nosso código usando uma modleo de linguagem da OpenAI, mais especificamente o modelo "gpt-4o-mini".
llm = ChatOpenAI(model_name="gpt-4o-mini")

#cria em variável com o tavily search, resposável por buscar em apenas 2 urls sobre os assunto colocado no input
tool = TavilySearch(max_results=2)

#aqui, apenas criamos uma lista de ferramentas, já que na classe abaixo, ele espera como resposta uma lista 
tools = [tool]

#aqui, definimos que a llm da openai vai usar os tools de busca em urls
llm_with_tools = llm.bind_tools(tools)


def chatbot(state: State):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

#essa classe será reponsável por chamar as ferramentas de busca em urls para que p chatbot consiga buscar informações na internet
class BasicToolNode:
    def __init__(self, tools: list) -> None:
        self.tools_by_name = {tool.name: tool for tool in tools}

    def __call__(self, inputs: dict):
        if messages := inputs.get("messages", []):
            message = messages[-1]
        else:
            raise ValueError("no messages found in inputs")
        outputs = []
        for tool_call in message.tool_calls: 
            tool_result = self.tools_by_name[tool_call["name"]].invoke(tool_call["args"])

            print("URLs retornadas pelo Tavily:")
            for item in tool_result.get("results", []):
                print("-", item.get("url"))

            outputs.append(ToolMessage(
                content=json.dumps(tool_result),
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"],
            )
            )

        return {"messages": outputs}
    
tool_node = BasicToolNode(tools = [tool])

#essa função tem como objetivo dar ou não a tool para o chatboot, ou seja, se a tool for chamada, o nó "tools" será ativado, caso contrário, o chatboot irá direto para o END
def route_tools(state: State,):
    if isinstance(state, list):
        ai_message = state[-1]
    elif messages := state.get("messages", []):
        ai_message = messages[-1]
    else:
        raise ValueError(f"No messages found in input state to tool_edge: {state}")
    if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
        return "tools"
    return END

#aqui terá como função principal construir as arestas entre os nós, ou seja, interligando cada ação/nó criados
graph_builder.add_conditional_edges(
    "chatbot",
    route_tools,
    {"tools": "tools", END: END},
)
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("tools", tool_node)
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
        user_input = input(" ")
        
        # Se o usuário digitar 'quit', 'exit' ou 'q', encerra o loop
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break
        
        # Caso contrário, chama a função para processar a entrada e responder
        stream_graph_updates(user_input)

    except:
            user_input = user_input

    events = graph.stream(
        {"messages": [{"role": "user", "content": user_input}]},
        config,
        stream_mode="values",
    )
    for event in events:
        event["messages"][-1].pretty_print()