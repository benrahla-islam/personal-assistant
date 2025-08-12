from langchain_community.tools import DuckDuckGoSearchRun
from langchain.tools import tool


@tool
def search_tool(query: str) -> str:
    """Search the web using DuckDuckGo."""
    search = DuckDuckGoSearchRun()
    result = search.run(query)
    return result