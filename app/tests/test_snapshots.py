import pytest

from quiz import allowlist, snapshots


@pytest.mark.parametrize("url,pkg,sym", [
    ("https://reference.langchain.com/python/langchain-chroma/vectorstores/Chroma", "langchain-chroma", "Chroma"),
    ("https://reference.langchain.com/python/langgraph.prebuilt/tool_node/ToolNode", "langgraph.prebuilt", "ToolNode"),
    ("https://reference.langchain.com/python/langchain-mcp-adapters/langchain_mcp_adapters/tools/load_mcp_tools",
     "langchain-mcp-adapters", "load_mcp_tools"),
])
def test_ref_target(url, pkg, sym):
    assert snapshots.ref_target(url) == (pkg, sym)


def test_ref_snapshot_name_matches_allowlist():
    url = "https://reference.langchain.com/python/langchain-chroma/vectorstores/Chroma"
    assert snapshots.ref_snapshot_name(url) == allowlist.snapshot_for(url, "api-ref")


def test_check_ref_text_rejects_wrong_symbol():
    assert snapshots.check_ref_text("# Chroma\n\n> **Class**", "Chroma") is None
    with pytest.raises(snapshots.SnapshotError):
        snapshots.check_ref_text("Symbol not found", "Chroma")
