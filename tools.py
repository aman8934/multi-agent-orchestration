from langchain.tools import tool
import requests
from bs4 import BeautifulSoup
from tavily import TavilyClient
import os
from rich import print
from dotenv import load_dotenv
load_dotenv()


tavily = TavilyClient(api_key = os.getenv("TAVILY_API_KEY"))

@tool
def web_search(query: str) -> str:
  """search the web for recent,relevant and reliable information on a topic .Return Titles , URLs and snippets"""
  results = tavily.search(query = query, max_results = 5)
  out= []
  for r in results['results']:
    out.append(
      f'Title:{r['title']}\nURL:{r['url']}\nSnippet:{r['content'][:300]}\n'
    )
  return "\n---\n".join(out)
# print(web_search.invoke("best remote job for data science or data analyst on which portal"))

@tool
def scrap_url(url: str) -> str:
  """Scrap and return clean text content from a given URLs"""
  try:
    content = requests.get(url,timeout=8,headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(content.text,"html.parser")
    for tag in soup(["script","style","nav", "footer"]):
      tag.decompose()
    return soup.get_text(separator=" ",strip = True)[:3000]
  
  except Exception as e:
    return f"coudn't scrap the URLS: {str(e)}"
# print(scrap_url.invoke("https://timesofindia.indiatimes.com/city/kanpur/drivers-body-found-56-hours-after-bus-plunged-into-canal/articleshow/130981950.cms"))