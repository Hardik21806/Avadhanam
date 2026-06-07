import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, MessagesState, START
from langchain_core.messages import SystemMessage

load_dotenv()

llm = ChatOpenAI(
    openai_api_base="https://api.groq.com/openai/v1",
    openai_api_key=os.getenv("GROQ_API_KEY"),
    model_name="llama-3.3-70b-versatile", # Groq's fastest, high-performing model
    temperature=0.7
)

sys_msg = SystemMessage(content="You are a helpful assistant.")

def assistant(state: MessagesState):
    return {"messages": [llm.invoke([sys_msg] + state['messages'])]}

builder = StateGraph(MessagesState)
builder.add_node("assistant", assistant)
builder.add_edge(START, "assistant")

config = {"configurable": {"thread_id": "1"}}