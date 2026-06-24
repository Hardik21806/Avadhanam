import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, MessagesState, START
from langchain_core.messages import SystemMessage

load_dotenv()

# Default values
DEFAULT_BASE_URL = "http://localhost:11434/v1"
DEFAULT_MODEL_NAME = "llama3.2:1b"
DEFAULT_API_KEY_ENV = None


def create_llm(base_url=None, model_name=None, api_key_env=None, temperature=0):
    """
    Dynamically create a ChatOpenAI LLM instance.
    
    Args:
        base_url: API base URL (default: Groq)
        model_name: Model name to use
        api_key_env: Environment variable name for API key
        temperature: Temperature for model sampling
    
    Returns:
        ChatOpenAI instance
    """
    base_url = base_url or DEFAULT_BASE_URL
    model_name = model_name or DEFAULT_MODEL_NAME
    api_key_env = api_key_env or DEFAULT_API_KEY_ENV or None
    
    if api_key_env:
        api_key = os.getenv(api_key_env)
    try :
        return ChatOpenAI(
            openai_api_base=base_url,
            openai_api_key=api_key,
            model_name=model_name,
            temperature=temperature
        )
    except Exception as e:
        print(e)
        return ChatOpenAI(
            openai_api_base=base_url,
            openai_api_key=None,
            model_name=model_name,
            temperature=temperature
        )


def create_agent_graph(base_url=None, model_name=None, api_key_env=None):
    """
    Dynamically create the agent graph and config.
    
    Args:
        base_url: API base URL
        model_name: Model name
        api_key_env: Environment variable name for API key
    
    Returns:
        Tuple of (builder, config, llm_instance)
    """
    llm = create_llm(base_url=base_url, model_name=model_name, api_key_env=api_key_env)
    sys_msg = SystemMessage(content="You are a helpful assistant.")
    
    def assistant(state: MessagesState):
        return {"messages": [llm.invoke([sys_msg] + state['messages'])]}
    
    builder = StateGraph(MessagesState)
    builder.add_node("assistant", assistant)
    builder.add_edge(START, "assistant")
    
    config = {"configurable": {"thread_id": "1"}}
    
    return builder, config, llm


# Default instances (for backward compatibility)
_llm = create_llm()
sys_msg = SystemMessage(content="You are a helpful assistant.")

def assistant(state: MessagesState):
    return {"messages": [_llm.invoke([sys_msg] + state['messages'])]}

builder = StateGraph(MessagesState)
builder.add_node("assistant", assistant)
builder.add_edge(START, "assistant")

config = {"configurable": {"thread_id": "1"}}