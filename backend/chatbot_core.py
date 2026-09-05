from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END, MessagesState
from synaptic import ChatbotMemory

load_dotenv()

# Initialize Synaptic Memory Engine (persisted in database/synaptic_memory.db)
memory = ChatbotMemory(db_path="database/synaptic_memory.db", use_neural_extractor=True)

llm = ChatGroq(
    model="qwen/qwen3.8-27b",
    temperature=0.5
)

def call_llm(state: MessagesState):
    response = llm.invoke(state["messages"])
    return {"messages": [response]}
   
graph = StateGraph(MessagesState)
graph.add_node("call_llm", call_llm)

graph.add_edge(START, "call_llm")
graph.add_edge("call_llm", END)
workflow = graph.compile()

if __name__ == "__main__":
    try:
        png_bytes = workflow.get_graph().draw_mermaid_png()
        with open("backend/chatbot_graph.png", "wb") as f:
            f.write(png_bytes)
        print("Saved Graph")
    except Exception as e:
        print("Unable to generate Graph.")
