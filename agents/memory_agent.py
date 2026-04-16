"""
Memory agent — persists conversation history to SQLite.
Uses LangChain SQLChatMessageHistory.
"""
from langchain_community.chat_message_histories import SQLChatMessageHistory
from langchain_core.messages import HumanMessage, AIMessage
import logging

logger = logging.getLogger(__name__)
DB_PATH = "sqlite:///portfolio_memory.db"

def get_session_history(session_id: str) -> SQLChatMessageHistory:
    return SQLChatMessageHistory(
        session_id= session_id,
        connection_string = DB_PATH,
    )

def add_interaction(session_id: str, user_input: str, ai_response: str):
    history = get_session_history(session_id)
    history.add_message(HumanMessage(content=user_input))
    history.add_message(AIMessage(content=ai_response))
    logger.info(f"Saved interaction to session {session_id}")

def get_recent_context(session_id:str, last_n: int=4) ->str:
    """Returns last N message pairs as a formatted string for prompt injection."""
    history = get_session_history(session_id)
    messages = history.messages[-last_n*2:]

    if not messages:
        return "No prior conversation context."
    
    lines =[]
    for msg in messages:
        role = "User" if isinstance(msg, HumanMessage) else "Assisstant"
        lines.append(f"{role}: {msg.content}")
    return "\n".join(lines)