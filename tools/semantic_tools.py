import json
import requests
import os
import re
import pathlib
from openai import OpenAI

ROOT = pathlib.Path(__file__).parent.parent

OM_HOST = "http://localhost:8585"
OM_TOKEN = "eyJraWQiOiJHYjM4OWEtOWY3Ni1nZGpzLWE5MmotMDI0MmJrOTQzNTYiLCJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJvcGVuLW1ldGFkYXRhLm9yZyIsInN1YiI6ImFkbWluIiwicm9sZXMiOlsiQWRtaW4iXSwiZW1haWwiOiJhZG1pbkBvcGVuLW1ldGFkYXRhLm9yZyIsImlzQm90IjpmYWxzZSwidG9rZW5UeXBlIjoiUEVSU09OQUxfQUNDRVNTIiwidXNlcm5hbWUiOiJhZG1pbiIsInByZWZlcnJlZF91c2VybmFtZSI6ImFkbWluIiwiaWF0IjoxNzc2NjEzMzQxLCJleHAiOjE3ODQzODkzNDF9.W_89SEYlaqQqUfQghq2fZ6814ujFeO6Vo-4LMQz-9FSzPhwv9aURPuKO0oEFV9QAUu90gBpUqrbGncPeGU_NPLWWQzVFNamjBXpc71xgSz71RY5KOgUNBl-AC5JNRqLX9_LmuvvgUEMzeLZMRzdmDLr8bUTe_z-T--QY_3SnKbQjDlSqNBO2Yk-HATU-CLh1WZigifLP3kdQmVhd0ORBhhecxTwSzW0e9UoEjHT_m3DNp44U5LYngGJ378FgZvTh5N-X5oW7qcuAGOkqbW5l-vrKolSJvsilE1MTGAJTzpc0M5rJZYoFZehuae3oXVOzJvFjfHA34IpfMBTM_X7jUg"

HEADERS = {
    "Authorization": f"Bearer {OM_TOKEN}",
    "Content-Type": "application/json"
}

import os
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = OpenAI(
    api_key=GROQ_KEY,
    base_url="https://api.groq.com/openai/v1"
)

# PII indicator keywords
PII_KEYWORDS = [
    "email", "phone", "mobile", "address", "name_", "_name",
    "password", "ssn", "dob", "birth", "credit", "card",
    "account", "license", "passport", "user_id", "userid",
    "ip_", "_ip", "location", "gender", "race", "salary"
]


def _get_tables_simple(limit: int = 30) -> list:
    """Get tables without heavy fields"""
    try:
        r = requests.get(
            f"{OM_HOST}/api/v1/tables",
            headers=HEADERS,
            params={"limit": limit},
            timeout=15
        )
        return r.json().get("data", [])
    except:
        return []


def _get_columns(table_id: str) -> list:
    """Get just column names for a table"""
    try:
        r = requests.get(
            f"{OM_HOST}/api/v1/tables/{table_id}",
            headers=HEADERS,
            params={"fields": "columns"},
            timeout=10
        )
        if r.status_code == 200:
            return [{"name": c["name"], "type": c.get("dataType", "")}
                    for c in r.json().get("columns", [])]
    except:
        pass
    return []


def auto_classify_pii(limit: int = 20) -> dict:
    """
    Automatically scan tables and detect PII columns
    using intelligent column name pattern analysis.
    No LLM needed — pure pattern matching, fast and reliable.
    """
    try:
        tables = _get_tables_simple(limit)
        findings = []
        total_pii = 0

        for t in tables:
            table_id = t.get("id")
            table_name = t.get("name", "")
            cols = _get_columns(table_id)

            suspected_pii = []
            for col in cols:
                col_lower = col["name"].lower()
                for keyword in PII_KEYWORDS:
                    if keyword in col_lower:
                        suspected_pii.append({
                            "column": col["name"],
                            "type": col["type"],
                            "matched_pattern": keyword
                        })
                        break

            if suspected_pii:
                total_pii += 1
                findings.append({
                    "table": table_name,
                    "pii_column_count": len(suspected_pii),
                    "suspected_pii": suspected_pii,
                    "risk_level": "HIGH" if len(suspected_pii) > 3 else "MEDIUM",
                    "recommendation": f"Review and tag {len(suspected_pii)} columns with PII.Sensitive"
                })

        return {
            "tables_scanned": len(tables),
            "tables_with_suspected_pii": total_pii,
            "tables_clean": len(tables) - total_pii,
            "overall_risk": "HIGH" if total_pii > 5 else "MEDIUM" if total_pii > 0 else "LOW",
            "findings": findings,
            "summary": f"Scanned {len(tables)} tables. Found suspected PII in {total_pii} tables based on column name analysis."
        }
    except Exception as e:
        return {"error": str(e)}


def semantic_search(user_intent: str, limit: int = 5) -> dict:
    """
    Semantic discovery — finds tables matching user intent
    using column name analysis without heavy LLM calls.
    """
    try:
        tables = _get_tables_simple(50)

        # Keywords from user intent
        intent_words = user_intent.lower().split()

        scored = []
        for t in tables:
            table_id = t.get("id")
            table_name = t.get("name", "").lower()
            cols = _get_columns(table_id)
            col_names = " ".join(c["name"].lower() for c in cols)

            # Score by matching intent words
            score = 0
            matched = []
            for word in intent_words:
                if len(word) < 3:
                    continue
                if word in table_name:
                    score += 3
                    matched.append(f"table name contains '{word}'")
                for col in cols:
                    if word in col["name"].lower():
                        score += 1
                        matched.append(f"column '{col['name']}' matches '{word}'")
                        break

            if score > 0:
                scored.append({
                    "table": t["name"],
                    "relevance_score": score,
                    "match_reasons": matched[:3],
                    "column_count": len(cols),
                    "sample_columns": [c["name"] for c in cols[:5]]
                })

        # Sort by score
        scored.sort(key=lambda x: x["relevance_score"], reverse=True)
        top = scored[:limit]

        return {
            "user_intent": user_intent,
            "tables_analyzed": len(tables),
            "relevant_tables_found": len(top),
            "results": top,
            "summary": f"Found {len(top)} tables relevant to '{user_intent}'"
        }
    except Exception as e:
        return {"error": str(e)}


def suggest_data_owners(limit: int = 20) -> dict:
    """
    Scan tables with no owners and suggest ownership
    based on table name patterns.
    """
    try:
        tables = _get_tables_simple(limit)
        suggestions = []
        unowned_count = 0

        for t in tables:
            owner = (t.get("owner") or {}).get("name", "")
            if not owner or owner == "unassigned":
                unowned_count += 1
                name = t.get("name", "").upper()

                if any(k in name for k in ["ACT_", "PROC_", "FLOW_", "TASK_"]):
                    team = "Platform / DevOps Team"
                elif any(k in name for k in ["USER_", "AUTH_", "IDENTITY_", "LOGIN_"]):
                    team = "Identity & Access Team"
                elif any(k in name for k in ["ORDER_", "PAYMENT_", "INVOICE_", "BILLING_"]):
                    team = "Finance Team"
                elif any(k in name for k in ["ANALYTIC_", "REPORT_", "METRIC_", "INSIGHT_"]):
                    team = "Analytics Team"
                elif any(k in name for k in ["PRODUCT_", "ITEM_", "CATALOG_", "INVENTORY_"]):
                    team = "Product Team"
                else:
                    team = "Data Engineering Team"

                suggestions.append({
                    "table": t["name"],
                    "suggested_owner": team,
                    "reason": f"Naming pattern suggests {team}"
                })

        return {
            "total_tables_scanned": len(tables),
            "unowned_tables": unowned_count,
            "owned_tables": len(tables) - unowned_count,
            "ownership_coverage": f"{round((len(tables) - unowned_count) / len(tables) * 100, 1)}%" if tables else "0%",
            "suggestions": suggestions,
            "summary": f"{unowned_count} of {len(tables)} tables have no owner. Ownership suggestions provided based on naming conventions."
        }
    except Exception as e:
        return {"error": str(e)}