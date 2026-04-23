import os, requests
import pathlib
from dotenv import load_dotenv

ROOT = pathlib.Path(__file__).parent.parent
load_dotenv(dotenv_path=ROOT / ".env", override=True)

OM_HOST = "http://localhost:8585"
OM_TOKEN = "eyJraWQiOiJHYjM4OWEtOWY3Ni1nZGpzLWE5MmotMDI0MmJrOTQzNTYiLCJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJvcGVuLW1ldGFkYXRhLm9yZyIsInN1YiI6ImFkbWluIiwicm9sZXMiOlsiQWRtaW4iXSwiZW1haWwiOiJhZG1pbkBvcGVuLW1ldGFkYXRhLm9yZyIsImlzQm90IjpmYWxzZSwidG9rZW5UeXBlIjoiUEVSU09OQUxfQUNDRVNTIiwidXNlcm5hbWUiOiJhZG1pbiIsInByZWZlcnJlZF91c2VybmFtZSI6ImFkbWluIiwiaWF0IjoxNzc2OTMwNjM0LCJleHAiOjE3ODQ3MDY2MzR9.v6fNDPumCCVkA1jax3OHaOfYvK--ubmfz_9u-pYsn18jI82pB_tumvh2U-Qs_zgCjHUVhLUJGqtUATaQ8TXr0rl0hl0B7z_rhAH8UOzKKxNZz3ZW8Tfe8UdBlMg2Q4UVCzUbesV40hiqDYZZcrHI7KILKOsFt4pCFRZbC_j7S9SO3MLrfVJtssvL6F2SZrG2Bdy7JUNHsmk3EfEuUb6LARODbaCRNqL9aXgu9bDuyqWW9yIGgVovsgJxXKhAPJWK7Qnuqhn0cS7FbPi7EjVd862rfs5_GhJCbCMchNKfsFmUO0W7zEgzX2a164ZN85V-FxSjWPDvhakvnTuzFLpFMg"
HEADERS = {
    "Authorization": f"Bearer {OM_TOKEN}",
    "Content-Type": "application/json"
}


def _headers():
    return HEADERS


def _get_all_tables(limit: int = 200) -> list:
    try:
        r = requests.get(
            f"{OM_HOST}/api/v1/tables",
            headers=HEADERS,
            params={"limit": limit},
            timeout=15
        )
        if r.status_code != 200:
            return []
        print(f"DEBUG _get_all_tables: status={r.status_code}, count={len(r.json().get('data', []))}")
        return r.json().get("data", [])
    except Exception as e:
        print(f"ERROR _get_all_tables: {e}")
        return []


def _find_table(table_name: str) -> dict:
    tables = _get_all_tables(200)
    for t in tables:
        if t["name"].lower() == table_name.lower():
            return t
    for t in tables:
        if table_name.lower() in t["name"].lower():
            return t
    return {}


def search_assets(query: str, asset_type: str = "all", limit: int = 10) -> dict:
    try:
        tables = _get_all_tables(200)
        if not tables:
            return {"error": "No tables found. Please add a data source in OpenMetadata."}
        query_lower = query.lower()
        results = []
        for t in tables:
            name = t.get("name", "")
            desc = t.get("description", "") or ""
            if query_lower in name.lower() or query_lower in desc.lower() or query == "*":
                results.append({
                    "name": name,
                    "type": "table",
                    "fqn": t.get("fullyQualifiedName", ""),
                    "description": desc[:200] or "No description",
                    "owner": (t.get("owner") or {}).get("name", "unassigned"),
                    "tags": [tg["tagFQN"] for tg in t.get("tags", [])]
                })
            if len(results) >= limit:
                break
        return {"query": query, "total": len(results), "results": results}
    except Exception as e:
        return {"error": str(e)}


def list_tables(limit: int = 20) -> dict:
    try:
        tables = _get_all_tables(limit)
        if not tables:
            return {"total": 0, "message": "No tables found. Please add a data source in OpenMetadata at http://localhost:8585", "tables": []}
        return {
            "total": len(tables),
            "note": f"Showing {len(tables)} tables from catalog",
            "tables": [{
                "name": t["name"],
                "fqn": t.get("fullyQualifiedName", ""),
                "description": (t.get("description") or "")[:150],
                "owner": (t.get("owner") or {}).get("name", "unassigned"),
                "columns": len(t.get("columns", [])),
                "tags": [tg["tagFQN"] for tg in t.get("tags", [])]
            } for t in tables]
        }
    except Exception as e:
        return {"error": str(e)}


def get_table_details(table_fqn: str) -> dict:
    try:
        name = table_fqn.split(".")[-1] if "." in table_fqn else table_fqn
        found = _find_table(name)
        if not found:
            return {"error": f"Table '{name}' not found. Use list_tables to see available tables."}
        table_id = found.get("id")
        r = requests.get(
            f"{OM_HOST}/api/v1/tables/{table_id}",
            headers=HEADERS,
            params={"fields": "columns,tags"},
            timeout=15
        )
        if r.status_code != 200:
            return {"error": f"Table fetch failed. Status: {r.status_code}"}
        t = r.json()
        return {
            "name": t["name"],
            "fqn": t.get("fullyQualifiedName", ""),
            "description": t.get("description", "No description"),
            "owner": (t.get("owner") or {}).get("name", "unassigned"),
            "tags": [tg["tagFQN"] for tg in t.get("tags", [])],
            "total_columns": len(t.get("columns", [])),
            "columns": [{
                "name": c["name"],
                "type": c.get("dataType", ""),
                "description": c.get("description", "")
            } for c in t.get("columns", [])]
        }
    except Exception as e:
        return {"error": str(e)}


def get_lineage(table_fqn: str, depth: int = 2) -> dict:
    try:
        name = table_fqn.split(".")[-1] if "." in table_fqn else table_fqn
        found = _find_table(name)
        if not found:
            return {"error": f"Table '{name}' not found"}
        table_id = found.get("id")
        r = requests.get(
            f"{OM_HOST}/api/v1/lineage/table/{table_id}",
            headers=HEADERS,
            params={"upstreamDepth": depth, "downstreamDepth": depth},
            timeout=15
        )
        lin = r.json()
        return {
            "table": name,
            "upstream_count": len(lin.get("upstreamEdges", [])),
            "downstream_count": len(lin.get("downstreamEdges", [])),
            "nodes": [n.get("name", "") for n in lin.get("nodes", [])[:15]],
            "message": "No lineage found — lineage is built when pipelines run" if not lin.get("nodes") else ""
        }
    except Exception as e:
        return {"error": str(e)}


def detect_pii(table_fqn: str) -> dict:
    try:
        name = table_fqn.split(".")[-1] if "." in table_fqn else table_fqn
        found = _find_table(name)
        if not found:
            return {"error": f"Table '{name}' not found"}
        table_id = found.get("id")
        r = requests.get(
            f"{OM_HOST}/api/v1/tables/{table_id}",
            headers=HEADERS,
            params={"fields": "columns,tags"},
            timeout=15
        )
        if r.status_code != 200:
            return {"error": f"Status: {r.status_code}"}
        t = r.json()
        pii, safe = [], []
        for col in t.get("columns", []):
            tags = [tg["tagFQN"] for tg in col.get("tags", [])]
            if any("PII" in tag for tag in tags):
                pii.append({
                    "column": col["name"],
                    "type": col.get("dataType", ""),
                    "pii_tags": tags
                })
            else:
                safe.append(col["name"])
        return {
            "table": t["name"],
            "total_columns": len(t.get("columns", [])),
            "pii_count": len(pii),
            "pii_columns": pii,
            "safe_columns": safe,
            "risk_level": "HIGH" if len(pii) > 3 else "MEDIUM" if pii else "LOW",
            "recommendation": "Immediate review required" if pii else "✅ No PII detected"
        }
    except Exception as e:
        return {"error": str(e)}


def get_data_quality(table_fqn: str) -> dict:
    try:
        name = table_fqn.split(".")[-1] if "." in table_fqn else table_fqn
        found = _find_table(name)
        if not found:
            return {"error": f"Table '{name}' not found"}
        table_id = found.get("id")
        r = requests.get(
            f"{OM_HOST}/api/v1/tables/{table_id}",
            headers=HEADERS,
            params={"fields": "testSuite"},
            timeout=15
        )
        if r.status_code != 200:
            return {"error": f"Status: {r.status_code}"}
        t = r.json()
        suite = t.get("testSuite", {})
        summary = suite.get("summary", {})
        total = summary.get("total", 0)
        success = summary.get("success", 0)
        health = round(success / total * 100, 1) if total > 0 else None
        return {
            "table": t["name"],
            "test_suite": suite.get("name", "No tests configured"),
            "total_tests": total,
            "passed": success,
            "failed": summary.get("failed", 0),
            "health_score": f"{health}%" if health else "No tests run yet",
            "status": "HEALTHY" if health and health >= 80 else "NEEDS ATTENTION" if health else "NO DATA"
        }
    except Exception as e:
        return {"error": str(e)}


def apply_tags(table_fqn: str, tags: list) -> dict:
    try:
        name = table_fqn.split(".")[-1] if "." in table_fqn else table_fqn
        found = _find_table(name)
        if not found:
            return {"error": f"Table '{name}' not found"}
        table_id = found.get("id")
        h = {**HEADERS, "Content-Type": "application/json-patch+json"}
        payload = [{"op": "add", "path": "/tags", "value": [
            {"tagFQN": tag, "source": "Classification",
             "labelType": "Manual", "state": "Confirmed"}
            for tag in tags
        ]}]
        r = requests.patch(
            f"{OM_HOST}/api/v1/tables/{table_id}",
            headers=h, json=payload, timeout=15
        )
        return {
            "success": r.status_code in [200, 201],
            "table": name,
            "tags_applied": tags,
            "message": "✅ Tags applied successfully!" if r.status_code in [200, 201] else f"❌ Failed: {r.text[:200]}"
        }
    except Exception as e:
        return {"error": str(e)}


def list_pipelines(limit: int = 10) -> dict:
    try:
        r = requests.get(
            f"{OM_HOST}/api/v1/pipelines",
            headers=HEADERS,
            params={"limit": limit},
            timeout=15
        )
        data = r.json().get("data", [])
        return {
            "total": len(data),
            "pipelines": [{
                "name": p["name"],
                "fqn": p.get("fullyQualifiedName", ""),
                "description": (p.get("description") or "")[:100]
            } for p in data]
        }
    except Exception as e:
        return {"error": str(e)}


def generate_governance_report(limit: int = 10) -> dict:
    try:
        tables = _get_all_tables(limit)
        if not tables:
            return {"error": "No tables found. Please add a data source first."}
        report = []
        for t in tables:
            table_id = t.get("id")
            name = t.get("name", "")
            r = requests.get(
                f"{OM_HOST}/api/v1/tables/{table_id}",
                headers=HEADERS,
                params={"fields": "columns,tags,testSuite"},
                timeout=15
            )
            if r.status_code != 200:
                continue
            data = r.json()
            cols = data.get("columns", [])
            pii_cols = [
                c["name"] for c in cols
                if any("PII" in tg["tagFQN"] for tg in c.get("tags", []))
            ]
            suite = data.get("testSuite", {})
            summary = suite.get("summary", {})
            total = summary.get("total", 0)
            success = summary.get("success", 0)
            health = round(success / total * 100, 1) if total > 0 else None
            report.append({
                "table": name,
                "columns": len(cols),
                "pii_columns": pii_cols,
                "pii_count": len(pii_cols),
                "risk": "HIGH" if len(pii_cols) > 3 else "MEDIUM" if pii_cols else "LOW",
                "health_score": f"{health}%" if health else "No tests",
                "tags": [tg["tagFQN"] for tg in data.get("tags", [])]
            })
        total_pii = sum(1 for r in report if r["pii_count"] > 0)
        return {
            "tables_scanned": len(report),
            "tables_with_pii": total_pii,
            "tables_clean": len(report) - total_pii,
            "overall_risk": "HIGH" if total_pii > 3 else "MEDIUM" if total_pii > 0 else "LOW",
            "report": report
        }
    except Exception as e:
        return {"error": str(e)}


TOOL_MAP = {
    "search_assets": search_assets,
    "list_tables": list_tables,
    "get_table_details": get_table_details,
    "get_lineage": get_lineage,
    "detect_pii": detect_pii,
    "get_data_quality": get_data_quality,
    "apply_tags": apply_tags,
    "list_pipelines": list_pipelines,
    "generate_governance_report": generate_governance_report,
}

TOOLS_SPEC = [
    {"type": "function", "function": {"name": "search_assets", "description": "Search for tables by keyword.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}, "asset_type": {"type": "string", "enum": ["table", "dashboard", "pipeline", "all"]}, "limit": {"type": "integer"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "list_tables", "description": "List all tables in the catalog.", "parameters": {"type": "object", "properties": {"limit": {"type": "integer"}}}}},
    {"type": "function", "function": {"name": "get_table_details", "description": "Get full schema and columns of a table.", "parameters": {"type": "object", "properties": {"table_fqn": {"type": "string"}}, "required": ["table_fqn"]}}},
    {"type": "function", "function": {"name": "get_lineage", "description": "Get upstream and downstream lineage.", "parameters": {"type": "object", "properties": {"table_fqn": {"type": "string"}, "depth": {"type": "integer"}}, "required": ["table_fqn"]}}},
    {"type": "function", "function": {"name": "detect_pii", "description": "Detect PII columns in a table.", "parameters": {"type": "object", "properties": {"table_fqn": {"type": "string"}}, "required": ["table_fqn"]}}},
    {"type": "function", "function": {"name": "get_data_quality", "description": "Get data quality test results.", "parameters": {"type": "object", "properties": {"table_fqn": {"type": "string"}}, "required": ["table_fqn"]}}},
    {"type": "function", "function": {"name": "apply_tags", "description": "Apply governance tags to a table.", "parameters": {"type": "object", "properties": {"table_fqn": {"type": "string"}, "tags": {"type": "array", "items": {"type": "string"}}}, "required": ["table_fqn", "tags"]}}},
    {"type": "function", "function": {"name": "list_pipelines", "description": "List data pipelines.", "parameters": {"type": "object", "properties": {"limit": {"type": "integer"}}}}},
    {"type": "function", "function": {"name": "generate_governance_report", "description": "Generate full governance compliance report.", "parameters": {"type": "object", "properties": {"limit": {"type": "integer"}}}}},
]