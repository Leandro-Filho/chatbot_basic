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

#aqui, a função desse diconario é: com o typeddict, colocar valores nos atributos que serão colocaddos em state e a variaveel message terá um acumulo de mensagens sem nenhuma sobreescrever por conta da função add_messages.
class State(TypedDict):
    messages: Annotated[str, add_messages] #aqui é resposaável por criar as mensagens e não deixar que sejam sobrepostas umas nas outras

graph_builder = StateGraph(State)

#aqui é feito a "criação" de uma llm dentro do nosso código usando uma modleo de linguagem da OpenAI, mais especificamente o modelo "gpt-4o-mini".
llm = ChatOpenAI(model_name="gpt-4o-mini")


def chatbot(state: State):
    return {"messages": [llm.invoke(state["messages"])]}


#aqui terá como função principal construir as arestas entre os nós, ou seja, interligando cada ação/nó criados
graph_builder.add_node("chatbot", chatbot)
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
        user_input = "What do you know about LangGraph?"
        
        # Mostra no console a mensagem do usuário padrão
        print("User: " + user_input)
        
        # Processa essa entrada padrão usando a mesma função
        stream_graph_updates(user_input)
        
        # Sai do loop após usar a entrada padrão
        break


#para interagir com o chat, primeiro deve entrar no ambiente virtual, onde da para instalar as bibliogtecas, usando o código "source .venv/bin/activate", depois basta entrar no terminal e digitar "python3 chatboot.py", assim se iniciará a conversa. Para sair, basta digitar "quint", "exit" e saíra da conversa.