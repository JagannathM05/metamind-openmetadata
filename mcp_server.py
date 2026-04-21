import asyncio
import json
import sys
import pathlib

ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types
from tools.openmetadata_tools import list_tables, get_table_details, detect_pii, get_data_quality, apply_tags, search_assets, generate_governance_report, get_lineage, list_pipelines
from tools.semantic_tools import auto_classify_pii, semantic_search, suggest_data_owners

app = Server("metamind-openmetadata")

TOOL_MAP = {
    "list_tables": list_tables,
    "search_assets": search_assets,
    "get_table_details": get_table_details,
    "detect_pii": detect_pii,
    "get_data_quality": get_data_quality,
    "apply_tags": apply_tags,
    "generate_governance_report": generate_governance_report,
    "get_lineage": get_lineage,
    "list_pipelines": list_pipelines,
    "auto_classify_pii": auto_classify_pii,
    "semantic_search": semantic_search,
    "suggest_data_owners": suggest_data_owners,
}

@app.list_tools()
async def list_tools():
    return [
        types.Tool(name="list_tables", description="List all tables in OpenMetadata catalog", inputSchema={"type": "object", "properties": {"limit": {"type": "integer"}}}),
        types.Tool(name="search_assets", description="Search for data assets by keyword", inputSchema={"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}),
        types.Tool(name="get_table_details", description="Get full schema and columns of a table", inputSchema={"type": "object", "properties": {"table_fqn": {"type": "string"}}, "required": ["table_fqn"]}),
        types.Tool(name="detect_pii", description="Detect PII columns in a table for compliance", inputSchema={"type": "object", "properties": {"table_fqn": {"type": "string"}}, "required": ["table_fqn"]}),
        types.Tool(name="get_data_quality", description="Get data quality test results for a table", inputSchema={"type": "object", "properties": {"table_fqn": {"type": "string"}}, "required": ["table_fqn"]}),
        types.Tool(name="apply_tags", description="Apply governance tags to a table in OpenMetadata", inputSchema={"type": "object", "properties": {"table_fqn": {"type": "string"}, "tags": {"type": "array", "items": {"type": "string"}}}, "required": ["table_fqn", "tags"]}),
        types.Tool(name="generate_governance_report", description="Generate full governance compliance report", inputSchema={"type": "object", "properties": {"limit": {"type": "integer"}}}),
        types.Tool(name="get_lineage", description="Get upstream and downstream data lineage", inputSchema={"type": "object", "properties": {"table_fqn": {"type": "string"}}, "required": ["table_fqn"]}),
        types.Tool(name="list_pipelines", description="List all data pipelines", inputSchema={"type": "object", "properties": {"limit": {"type": "integer"}}}),
        types.Tool(name="auto_classify_pii", description="Auto-scan tables and detect PII by column name patterns", inputSchema={"type": "object", "properties": {"limit": {"type": "integer"}}}),
        types.Tool(name="semantic_search", description="Find tables matching user intent semantically", inputSchema={"type": "object", "properties": {"user_intent": {"type": "string"}, "limit": {"type": "integer"}}, "required": ["user_intent"]}),
        types.Tool(name="suggest_data_owners", description="Suggest data owners for unowned tables", inputSchema={"type": "object", "properties": {"limit": {"type": "integer"}}}),
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict):
    fn = TOOL_MAP.get(name)
    if not fn:
        return [types.TextContent(type="text", text=f"Unknown tool: {name}")]
    try:
        result = fn(**(arguments or {}))
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
    except Exception as e:
        return [types.TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def main():
    print("🧠 MetaMind MCP Server starting...", file=sys.stderr)
    print("📡 OpenMetadata: http://localhost:8585", file=sys.stderr)
    print("🛠️  12 tools available", file=sys.stderr)
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())