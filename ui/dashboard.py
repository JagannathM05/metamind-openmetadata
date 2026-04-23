import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.openmetadata_tools import _get_all_tables
from tools.semantic_tools import auto_classify_pii

st.set_page_config(page_title="MetaMind Dashboard", page_icon="📊", layout="wide")

st.markdown("""<style>
.stMetric {background:#1E3A5F;border-radius:12px;padding:16px;color:white}
</style>""", unsafe_allow_html=True)


def get_dashboard_stats():
    tables = _get_all_tables(168)
    total = len(tables)

    if total == 0:
        return {"total_tables": 0, "no_owner": 0, "no_description": 0,
                "with_tags": 0, "pii_tables": 0, "governance_score": 0,
                "tables": [], "empty": True}

    no_owner = sum(1 for t in tables
                   if not (t.get("owner") or {}).get("name")
                   or (t.get("owner") or {}).get("name") == "unassigned")
    no_description = sum(1 for t in tables if not t.get("description"))
    with_tags = sum(1 for t in tables if t.get("tags"))

    pii_result = auto_classify_pii(20)
    pii_tables = pii_result.get("tables_with_suspected_pii", 0)
    scanned = max(pii_result.get("tables_scanned", 1), 1)

    score_components = [
        (total - no_owner) / total * 25,
        (total - no_description) / total * 25,
        with_tags / total * 25,
        (scanned - pii_tables) / scanned * 25
    ]
    governance_score = round(sum(score_components), 1)

    return {
        "total_tables": total,
        "no_owner": no_owner,
        "no_description": no_description,
        "with_tags": with_tags,
        "pii_tables": pii_tables,
        "governance_score": governance_score,
        "tables": tables[:10],
        "empty": False
    }


st.markdown("# 📊 MetaMind — Catalog Health Dashboard")
st.markdown("*Real-time governance intelligence powered by OpenMetadata*")
st.divider()

with st.spinner("🔍 Scanning your catalog..."):
    stats = get_dashboard_stats()

if stats.get("empty"):
    st.warning("⚠️ No tables found in catalog. Please add a data source in OpenMetadata first.")
    st.info("Go to http://localhost:8585 → Settings → Services → Database Services → Add New Service")
    st.markdown("**Quick Setup:** Add MySQL service with host `mysql:3306`, user `openmetadata_user`, password `openmetadata_password`")
    st.stop()

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("📋 Total Tables", stats["total_tables"])
with col2:
    st.metric("👤 No Owner", stats["no_owner"],
              delta=f"-{round(stats['no_owner']/stats['total_tables']*100)}%",
              delta_color="inverse")
with col3:
    st.metric("📝 No Description", stats["no_description"],
              delta=f"-{round(stats['no_description']/stats['total_tables']*100)}%",
              delta_color="inverse")
with col4:
    st.metric("🏷️ Tagged Tables", stats["with_tags"])
with col5:
    st.metric("🎯 Governance Score", f"{stats['governance_score']}%")

st.divider()

col_left, col_right = st.columns([1, 2])

with col_left:
    score = stats["governance_score"]
    if score >= 80:
        status = "🟢 HEALTHY"
        color = "#22C55E"
    elif score >= 60:
        status = "🟡 NEEDS ATTENTION"
        color = "#F59E0B"
    else:
        status = "🔴 CRITICAL"
        color = "#EF4444"

    owned_pct = round((stats['total_tables'] - stats['no_owner']) / stats['total_tables'] * 100)
    desc_pct = round((stats['total_tables'] - stats['no_description']) / stats['total_tables'] * 100)
    tag_pct = round(stats['with_tags'] / stats['total_tables'] * 100)

    st.markdown(f"""
    <div style='background:#1E3A5F;border-radius:16px;padding:30px;text-align:center;color:white'>
        <div style='font-size:4rem;font-weight:900;color:{color}'>{score}%</div>
        <div style='font-size:1.2rem;margin-top:10px'>Governance Score</div>
        <div style='font-size:1rem;margin-top:8px'>{status}</div>
        <hr style='border-color:rgba(255,255,255,0.2);margin:16px 0'>
        <div style='text-align:left;font-size:0.85rem;opacity:0.8'>
        ✓ Ownership: {owned_pct}%<br>
        ✓ Descriptions: {desc_pct}%<br>
        ✓ Tag Coverage: {tag_pct}%<br>
        ✓ PII Reviewed: {round((20 - stats['pii_tables']) / 20 * 100)}%
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_right:
    st.markdown("### 🚨 Action Items")
    if stats["no_owner"] > 0:
        st.error(f"⚠️ **{stats['no_owner']} tables** have no assigned owner")
    if stats["no_description"] > 0:
        st.warning(f"📝 **{stats['no_description']} tables** have no description")
    if stats["pii_tables"] > 0:
        st.error(f"🛡️ **{stats['pii_tables']} tables** have suspected PII columns")
    if stats["with_tags"] < stats["total_tables"] * 0.5:
        st.warning(f"🏷️ Only **{stats['with_tags']} tables** are tagged")
    if score >= 80:
        st.success("✅ Your catalog is in great shape!")

    st.markdown("### 📈 Coverage Breakdown")
    st.progress(owned_pct / 100, text=f"Ownership: {owned_pct}%")
    st.progress(desc_pct / 100, text=f"Descriptions: {desc_pct}%")
    st.progress(tag_pct / 100, text=f"Tag Coverage: {tag_pct}%")

st.divider()
st.markdown("### 📋 Recent Tables in Catalog")

if stats["tables"]:
    data = []
    for t in stats["tables"]:
        data.append({
            "Table": t["name"],
            "Columns": len(t.get("columns", [])),
            "Owner": (t.get("owner") or {}).get("name", "⚠️ unassigned"),
            "Tags": ", ".join(tg["tagFQN"] for tg in t.get("tags", [])) or "none",
            "Description": (t.get("description") or "❌ missing")[:60]
        })
    st.dataframe(data, use_container_width=True, height=300)

st.divider()
st.markdown("*🧠 MetaMind — Built for Back to the Metadata Hackathon 2026 | WeMakeDevs × OpenMetadata*")