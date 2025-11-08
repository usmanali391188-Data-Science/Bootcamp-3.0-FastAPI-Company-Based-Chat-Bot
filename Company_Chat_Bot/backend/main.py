
from fastapi import FastAPI
from pydantic import BaseModel
import requests, re, os, csv
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

GEMINI_MODEL = "gemini-2.5-flash"
SCRAPE_TIMEOUT = 10

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("GEMINI_API_KEY not set in .env")

genai.configure(api_key=api_key)

app = FastAPI(title="Company Chatbot API")

class CompanyRequest(BaseModel):
    name: str
    website: str

class ChatRequest(BaseModel):
    question: str
    company: dict

def clean_text(text: str) -> str:
    return re.sub(r'\s+', ' ', text).strip() if text else ""

def scrape_website(name: str, url: str) -> dict:
    if not url.startswith("http"):
        url = "https://" + url
    url = url.rstrip("/")

    try:
        res = requests.get(url, timeout=SCRAPE_TIMEOUT, headers={"User-Agent": "Mozilla/5.0"})
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')

        desc = ""
        meta = soup.find("meta", {"name": re.compile("description", re.I)})
        if meta and (content := meta.get("content")):
            desc = clean_text(content)
        else:
            for p in soup.find_all("p"):
                txt = clean_text(p.get_text())
                if txt and 30 < len(txt) < 500:
                    desc = txt
                    break
            if not desc:
                desc = f"Welcome to {name}!"

        logo = None
        for sel in ["img[alt*='logo' i']", ".logo img", "header img",
                    'link[rel="icon"]', 'link[rel="shortcut icon"]', 'meta[property="og:image"]']:
            tag = soup.select_one(sel)
            if tag:
                src = tag.get("src") or tag.get("href") or tag.get("content")
                if src:
                    logo = urljoin(url, src)
                    break

        body = soup.find("body")
        context = clean_text(body.get_text())[:4000] if body else f"{name} website."

        return {
            "name": name,
            "website": url,
            "description": desc[:300] + "..." if len(desc) > 300 else desc,
            "logo": logo,
            "context": context
        }

    except:
        return {
            "name": name,
            "website": url,
            "description": f"Welcome to {name}!",
            "logo": None,
            "context": f"{name} is at {url}."
        }

def save_chat_to_csv(chat_list: list, filename="chat_history.csv"):
    with open(filename, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for msg in chat_list:
            writer.writerow([msg["role"], msg["content"]])

def ask_gemini(question: str, company_data: dict) -> str:
    prompt = f"""
You are the official chatbot for {company_data['name']}.
Website: {company_data['website']}
About: {company_data['description']}

Answer in the same language as the user. 
You can respond in any language, including English, Urdu, French, Spanish, Arabic, etc.
Use website context if needed.

Context:
{company_data['context'][:3000]}

Question: {question}
Answer in 1-2 sentences.
"""
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error: {str(e)[:100]}"

@app.post("/scrape")
def api_scrape(company: CompanyRequest):
    return scrape_website(company.name, company.website)

@app.post("/chat")
def api_chat(req: ChatRequest):
    reply = ask_gemini(req.question, req.company)
    save_chat_to_csv([
        {"role": "user", "content": req.question},
        {"role": "assistant", "content": reply}
    ])
    return {"reply": reply}


















































