from tavily import TavilyClient
from duckduckgo_search import DDGS
import os


tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


def tavily_search(query: str, max_results: int = 5) -> list:
    """
    Searches web using Tavily.
    Returns list of clean results.
    """
    try:
        response = tavily_client.search(
            query=query,
            search_depth="advanced",
            max_results=max_results,
            include_answer=True
        )

        results = []
        for item in response.get("results", []):
            results.append({
                "title": item.get("title", ""),
                "content": item.get("content", ""),
                "url": item.get("url", ""),
                "score": item.get("score", 0)
            })

        return results

    except Exception as e:
        print(f"Tavily search failed: {e}")
        return duckduckgo_search(query, max_results)


def duckduckgo_search(query: str, max_results: int = 5) -> list:
    """
    Fallback search using DuckDuckGo.
    """
    try:
        results = []
        with DDGS() as ddgs:
            for result in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": result.get("title", ""),
                    "content": result.get("body", ""),
                    "url": result.get("href", ""),
                    "score": 0.5
                })
        return results

    except Exception as e:
        print(f"DuckDuckGo search failed: {e}")
        return []
