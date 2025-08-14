#importar Annotated é importante para colocar-mos mais contexto em algumas informações para que o chatboot consiga organizar suas funções e ações da melhor forma possível
from typing import Annotated

#no tutorial, ele importa o TypedDict com typing_extensions, mas como estamos usando o python3.12, não precisamos usar esse comendo, conseguimos importar pelo typing direto
# aqui, a função do TypedDict é a função de definir um unico valor ou tipo de variável que será coloccada em cada atributo, fazendo com que não seja mais dinâmico e trave os valores apenas para o que queremos.
from typing import TypedDict

#aqui importamos o stategraph, starte end, funções fundamentais para o chatboot. o start gtem como função definir o começo de onde começará o nó, o end definará o final dele e o stategraph fará todo o corpo do chatboot, desde os nós e arestas quanto os valores que serão depositados em cada variável.
from langgraph.graph import StateGraph, START, END

from langgraph.graph.message import add_messages

#aqui será carregado a biblioteca para criar um ambiente possivel para colocar a chave de api da openai
from dotenv import load_dotenv
load_dotenv()

#aqui, será importado o ChatOpenai, ou seja, o modelo de linguagem da OpenAI será usado como base do nosso chatboot.
from langchain_openai import ChatOpenAI

#aqui, importamos o tavily, responsável por fazer a buscar em url sobre o iput que será colocado
from langchain_tavily import TavilySearch

import json

from langchain_core.messages import ToolMessage

#cria em variável com o tavily search, resposável por buscar em apenas 2 urls sobre os assunto colocado no input
tool = TavilySearch(max_results=2)

#aqui, apenas criamos uma lista de ferramentas, já que na classe abaixo, ele espera como resposta uma lista 
tools = [tool]

#aqui, será feita a busca pela a variável tool, que tem a tavily para buscar pelas url sobre "What is a dog?"
tool.invoke("What is a dog?")

#aqui, a função desse diconario é: com o typeddict, colocar valores nos atributos que serão colocaddos em state e a variaveel message terá um acumulo de mensagens sem nenhuma sobreescrever por conta da função add_messages.
class State(TypedDict):
    messages: Annotated[str, add_messages] #aqui é resposaável por criar as mensagens e não deixar que sejam sobrepostas umas nas outras

graph_builder = StateGraph(State)

#aqui é feito a "criação" de uma llm dentro do nosso código usando uma modleo de linguagem da OpenAI, mais especificamente o modelo "gpt-4o-mini".
llm = ChatOpenAI(model_name="gpt-4o-mini")

#aqui, definimos que a llm da openai vai usar os tools de busca em urls
llm_with_tools = llm.bind_tools(tools)


def chatbot(state: State):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

#essa classe será reponsável por chamar as ferramentas de busca em urls para que p chatbot consiga buscar informações na internet
class BasicToolNode:
    def __init__(self, tools: list) -> None:
        self.tools_by_name = {tool.name: tool for tool in tool}

    def __call__(self, inputs: dict):
        if messages := inputs.get("messages", []):
            message = messages[-1]
        else:
            raise ValueError("no messages found in inputs")
        outputs = []
        for tool_call in message.tool_calls: 
            tool_result = self.tools_by_name[tool_call["name"]].invoke(tool.call["args"])
            outputs.append(ToolMessage(
                content=json.dumps(tool_result),
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"],
            )
            )
        
        return {"messages": outputs}
    
tool_node = BasicToolNode(tool = [tool])


def route_tool(state: State,):
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
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("tools", tool_node)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)
graph = graph_builder.compile()

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
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break
        
        # Caso contrário, chama a função para processar a entrada e responder
        stream_graph_updates(user_input)

    # Caso ocorra qualquer erro durante a execução (try/except sem tipo captura todos os erros)
    except:
        # Define uma entrada padrão (fallback) caso aconteça algum erro
        user_input = "What is a dog?"
        
        # Mostra no console a mensagem do usuário padrão
        print("User: " + user_input)
        
        # Processa essa entrada padrão usando a mesma função
        stream_graph_updates(user_input)
        
        # Sai do loop após usar a entrada padrão
        break


#para interagir com o chat, primeiro deve entrar no ambiente virtual, onde da para instalar as bibliogtecas, usando o código "source .venv/bin/activate", depois basta entrar no terminal e digitar "python3 chatboot.py", assim se iniciará a conversa. Para sair, basta digitar "quint", "exit" e saíra da conversa.