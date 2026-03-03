from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any

import requests
from bs4 import BeautifulSoup


@dataclass
class ResearchResult:
    source: str
    title: str
    url: str
    snippet: str


def fetch_news_headlines(query: str, max_results: int = 10) -> List[ResearchResult]:
    """
    Very simple news search using a generic web search endpoint.
    NOTE: This is a prototype and may need to be adapted to specific APIs
    (e.g. NewsAPI, custom search) in production.
    """
    results: List[ResearchResult] = []
    try:
        resp = requests.get(
            "https://news.google.com/search",
            params={"q": query, "hl": "en-IN"},
            timeout=5,
        )
        resp.raise_for_status()
    except Exception:
        return results

    soup = BeautifulSoup(resp.text, "html.parser")
    articles = soup.select("article")[:max_results]
    for art in articles:
        title_el = art.select_one("h3")
        if not title_el or not title_el.text:
            continue
        link_el = title_el.find("a")
        url = ""
        if link_el and link_el.get("href"):
            href = link_el["href"]
            if href.startswith("./"):
                url = "https://news.google.com" + href[1:]
            else:
                url = href
        snippet = ""
        results.append(
            ResearchResult(
                source="news",
                title=title_el.text.strip(),
                url=url,
                snippet=snippet,
            )
        )

    return results


def summarize_research(company_name: str, sector: str | None = None) -> Dict[str, Any]:
    """
    High-level wrapper to collect external research signals.
    Currently only news headlines; MCA/e-Courts can be added similarly.
    """
    query_parts = [company_name]
    if sector:
        query_parts.append(sector)
    query = " ".join(query_parts)
    headlines = fetch_news_headlines(query)

    titles = [h.title for h in headlines]
    urls = [h.url for h in headlines]

    # Very lightweight risk heuristics over news titles
    litigation_words = ["litigation", "lawsuit", "suit", "case", "dispute", "tribunal"]
    headwind_words = ["slowdown", "crisis", "headwind", "pressure", "stress", "default", "downgrade", "insolvency"]

    litigation_news_count = 0
    headwind_hits = 0
    for t in titles:
        tl = t.lower()
        if any(w in tl for w in litigation_words):
            litigation_news_count += 1
        if any(w in tl for w in headwind_words):
            headwind_hits += 1

    headline_count = len(titles)
    sector_headwind_score = float(headwind_hits / headline_count) if headline_count else 0.0

    return {
        "research_news_headline_count": headline_count,
        "research_news_titles": titles[:5],
        "research_news_urls": urls[:5],
        "research_litigation_news_count": litigation_news_count,
        "research_sector_headwind_score": sector_headwind_score,
    }

