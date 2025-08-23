from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain.tools import tool


@tool
def search_tool(query: str) -> str:
    """Search the web using DuckDuckGo."""
    search = DuckDuckGoSearchRun()
    result = search.run(query)
    return result


@tool
def wiki_search_tool(query: str) -> str:
    """Search Wikipedia."""
    wikipedia = WikipediaAPIWrapper()
    search = WikipediaQueryRun(api_wrapper=wikipedia)
    result = search.run(query)
    return result
