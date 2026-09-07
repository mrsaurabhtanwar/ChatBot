import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END, MessagesState
load_dotenv()

llm = ChatGroq(
    model=os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b"),
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
