import os, json, re
import pathlib
from dotenv import load_dotenv

ROOT = pathlib.Path(__file__).parent.parent
load_dotenv(dotenv_path=ROOT / ".env", override=True)

from openai import OpenAI
from tools.openmetadata_tools import TOOL_MAP as BASE_TOOL_MAP
from tools.semantic_tools import semantic_search, auto_classify_pii, suggest_data_owners

GROQ_KEY = os.getenv("GROQ_API_KEY")
print(f"DEBUG: GROQ key = {GROQ_KEY[:10] if GROQ_KEY else 'NOT FOUND'}")

if not GROQ_KEY:
    raise ValueError("GROQ_API_KEY not found!")

client = OpenAI(
    api_key=GROQ_KEY,
    base_url="https://api.groq.com/openai/v1"
)

TOOL_MAP = {
    **BASE_TOOL_MAP,
    "semantic_search": semantic_search,
    "auto_classify_pii": auto_classify_pii,
    "suggest_data_owners": suggest_data_owners,
}

SYSTEM_PROMPT = """You are MetaMind, an AI agent for OpenMetadata at localhost:8585 with 168 real tables.

Respond ONLY with JSON to call tools:
{"tool": "tool_name", "args": {"key": "value"}}

TOOLS:
- list_tables: {"tool": "list_tables", "args": {"limit": 20}}
- search_assets: {"tool": "search_assets", "args": {"query": "keyword"}}
- get_table_details: {"tool": "get_table_details", "args": {"table_fqn": "TABLE_NAME"}}
- detect_pii: {"tool": "detect_pii", "args": {"table_fqn": "TABLE_NAME"}}
- get_data_quality: {"tool": "get_data_quality", "args": {"table_fqn": "TABLE_NAME"}}
- get_lineage: {"tool": "get_lineage", "args": {"table_fqn": "TABLE_NAME"}}
- apply_tags: {"tool": "apply_tags", "args": {"table_fqn": "TABLE_NAME", "tags": ["PII.Sensitive"]}}
- generate_governance_report: {"tool": "generate_governance_report", "args": {"limit": 10}}
- auto_classify_pii: {"tool": "auto_classify_pii", "args": {"limit": 20}}
- suggest_data_owners: {"tool": "suggest_data_owners", "args": {"limit": 20}}
- semantic_search: {"tool": "semantic_search", "args": {"user_intent": "what user needs"}}
- list_pipelines: {"tool": "list_pipelines", "args": {}}
- final_answer: {"tool": "final_answer", "args": {"answer": "formatted response with emojis"}}

RULES:
1. ALWAYS call a data tool first
2. NEVER say catalog is empty — 168 real tables exist
3. After getting data call final_answer with formatted response
4. Use emojis and clear sections
5. ONLY respond with JSON"""


def parse_tool_call(text: str) -> dict:
    text = text.strip()
    text = re.sub(r'```(?:json)?\s*', '', text)
    text = re.sub(r'```', '', text).strip()
    try:
        return json.loads(text)
    except:
        pass
    match = re.search(r'\{[^{}]*"tool"[^{}]*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except:
            pass
    match = re.search(r'\{.*?\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except:
            pass
    return {}


def run_agent(user_message: str, history: list = []) -> str:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in history[-6:]:
        messages.append({"role": msg["role"], "content": str(msg["content"])})
    messages.append({"role": "user", "content": user_message})

    for iteration in range(6):
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                max_tokens=1024,
                temperature=0
            )
        except Exception as e:
            err = str(e)
            if "rate_limit" in err or "429" in err:
                try:
                    response = client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=messages,
                        max_tokens=1024,
                        temperature=0
                    )
                except Exception as e2:
                    return f"❌ API error: {str(e2)}"
            else:
                return f"❌ API error: {err}"

        reply = response.choices[0].message.content or ""
        print(f"🤖 [{iteration}]: {reply[:150]}")

        tool_call = parse_tool_call(reply)

        if not tool_call or "tool" not in tool_call:
            messages.append({"role": "assistant", "content": reply})
            messages.append({"role": "user", "content": 'Respond with ONLY JSON: {"tool": "list_tables", "args": {}}'})
            continue

        tool_name = tool_call.get("tool", "").strip()
        tool_args = tool_call.get("args", {})
        if not isinstance(tool_args, dict):
            tool_args = {}

        print(f"🔧 {tool_name}({tool_args})")

        if tool_name == "final_answer":
            return tool_args.get("answer", reply)

        tool_fn = TOOL_MAP.get(tool_name)
        if tool_fn:
            try:
                result = tool_fn(**tool_args)
            except Exception as e:
                result = {"error": str(e)}
        else:
            result = {"error": f"Unknown tool: {tool_name}"}

        print(f"📦 {str(result)[:200]}")

        messages.append({"role": "assistant", "content": reply})
        messages.append({
            "role": "user",
            "content": f"Tool result:\n{json.dumps(result, indent=2)}\n\nNow call final_answer with formatted response using emojis."
        })

    return "⚠️ Could not complete. Please try again."