"""Tests for Obsidian Second Brain Wiki, Audit, and Sync REST API endpoints."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Generator

import pytest

from neuro_memory_daemon import MemoryDaemon
from neuro_memory_daemon.mcp_server import MCPServer
from neuro_memory_daemon.ui_server import MemoryUIServer, start_server_in_thread, _parse_wiki_article
from tests.test_ui_server import get_free_port, _http_get, _http_post


@pytest.fixture
def obsidian_server(temp_dir: Path) -> Generator[tuple[MemoryUIServer, str, MemoryDaemon], None, None]:
    """Start an ephemeral test server for Obsidian API testing."""
    port = get_free_port()
    db_file = temp_dir / "obsidian_test_db.json"
    daemon = MemoryDaemon(db_path=db_file)

    pub_dir = Path(__file__).resolve().parent.parent / "public"
    server = start_server_in_thread(
        host="127.0.0.1",
        port=port,
        daemon=daemon,
        public_dir=pub_dir,
    )
    base_url = f"http://127.0.0.1:{port}"

    yield server, base_url, daemon

    server.stop()


def test_parse_wiki_article_unit(temp_dir: Path):
    """Test unit parsing of Obsidian Flavored Markdown with YAML frontmatter & callout."""
    wiki_file = temp_dir / "Test Article.md"
    content = """---
title: "Test Architecture Article"
created: 2026-10-26T02:00:00Z
updated: 2026-10-26T02:30:00Z
confidence: 0.98
stdp_engrams: 42
status: CANONICAL
category: Architecture
tags: [test, architecture, zothos]
---

> [!abstract] Executive Summary
> This is a test executive summary synthesized by Karpathy LLM Wiki engine.
> It tests multi-line callout extraction.

## Core Pillars
Here is the body content with [[Internal Wikilink]].
"""
    wiki_file.write_text(content, encoding="utf-8")

    article = _parse_wiki_article(wiki_file)
    assert article["title"] == "Test Architecture Article"
    assert article["created"] == "2026-10-26T02:00:00Z"
    assert article["updated"] == "2026-10-26T02:30:00Z"
    assert article["confidence"] == 0.98
    assert article["stdp_engrams"] == 42
    assert article["status"] == "CANONICAL"
    assert article["category"] == "Architecture"
    assert "test" in article["tags"]
    assert "architecture" in article["tags"]
    assert "This is a test executive summary" in article["executive_summary"]
    assert "## Core Pillars" in article["body"]


def test_obsidian_wiki_get(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test GET /api/obsidian/wiki returns synthesized wiki articles."""
    _, base_url, _ = obsidian_server
    status, _, body = _http_get(f"{base_url}/api/obsidian/wiki")
    assert status == 200
    data = json.loads(body.decode("utf-8"))
    assert data["ok"] is True
    assert "count" in data
    assert data["count"] >= 6
    assert "articles" in data
    titles = [a["title"] for a in data["articles"]]
    assert any("Vaelor" in t for t in titles)
    assert any("Biomorphic STDP" in t for t in titles)


def test_obsidian_audit_get(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test GET /api/obsidian/audit returns doctor audit metrics."""
    _, base_url, _ = obsidian_server
    status, _, body = _http_get(f"{base_url}/api/obsidian/audit")
    assert status == 200
    data = json.loads(body.decode("utf-8"))
    assert data["ok"] is True
    assert data["score"] == 100
    assert data["status"] in ("PERFECT", "HEALTHY")
    assert data["canvasesValid"] >= 6
    assert data["basesValid"] >= 5
    assert data["totalNotes"] >= 1000
    assert data["connectivityPct"] > 90.0


def test_obsidian_status_get(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test GET /api/obsidian/status returns vault inventory."""
    _, base_url, _ = obsidian_server
    status, _, body = _http_get(f"{base_url}/api/obsidian/status")
    assert status == 200
    data = json.loads(body.decode("utf-8"))
    assert data["ok"] is True
    assert "vaultPath" in data
    assert "canvases" in data
    assert "bases" in data
    assert "wikiArticles" in data
    assert len(data["canvases"]) >= 6
    assert len(data["bases"]) >= 5
    assert len(data["wikiArticles"]) >= 6


def test_obsidian_wiki_post_validation(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test POST /api/obsidian/wiki requires topic."""
    _, base_url, _ = obsidian_server
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        _http_post(f"{base_url}/api/obsidian/wiki", {"topic": ""})
    assert exc_info.value.code == 400


def test_obsidian_wiki_post_synthesize(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test POST /api/obsidian/wiki synthesizes topic and ingests memory."""
    _, base_url, daemon = obsidian_server
    status, _, body = _http_post(f"{base_url}/api/obsidian/wiki", {
        "topic": "Vaelor Account-Lattice & PoUW Protocol"
    })
    assert status == 201
    data = json.loads(body.decode("utf-8"))
    assert data["ok"] is True
    assert data["status"] == "synthesized"
    assert "article" in data
    assert "Vaelor" in data["article"]["title"]


def test_obsidian_sync_post(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test POST /api/obsidian/sync synchronizes vault artifacts into daemon memories."""
    _, base_url, daemon = obsidian_server
    status, _, body = _http_post(f"{base_url}/api/obsidian/sync", {})
    assert status == 200
    data = json.loads(body.decode("utf-8"))
    assert data["ok"] is True
    assert data["status"] == "synced"
    assert "canvases" in data
    assert "bases" in data
    assert "wikiArticles" in data
    assert len(data["canvases"]) >= 6
    assert len(data["bases"]) >= 5


def test_obsidian_canvases_get(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test GET /api/obsidian/canvases returns parsed JSON Canvas 1.0 topologies."""
    _, base_url, _ = obsidian_server
    status, _, body = _http_get(f"{base_url}/api/obsidian/canvases")
    assert status == 200
    data = json.loads(body.decode("utf-8"))
    assert data["ok"] is True
    assert "count" in data
    assert data["count"] >= 14
    assert "canvases" in data
    canvases = data["canvases"]
    names = [c["name"] for c in canvases]
    assert any("Pillars" in n for n in names)
    assert any("Vaelor" in n for n in names)
    assert any("Marketplace" in n for n in names)
    for c in canvases:
        assert "name" in c
        assert "relPath" in c
        assert "nodeCount" in c
        assert "edgeCount" in c
        assert "groupCount" in c
        assert "nodes" in c
        assert "edges" in c


def test_obsidian_bases_get(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test GET /api/obsidian/bases returns parsed Obsidian Bases YAML databases."""
    _, base_url, _ = obsidian_server
    status, _, body = _http_get(f"{base_url}/api/obsidian/bases")
    assert status == 200
    data = json.loads(body.decode("utf-8"))
    assert data["ok"] is True
    assert "count" in data
    assert data["count"] >= 18
    assert "bases" in data
    bases = data["bases"]
    names = [b["name"] for b in bases]
    assert any("Tools" in n for n in names)
    assert any("Fleet" in n for n in names)
    assert any("Wiki" in n for n in names)
    for b in bases:
        assert "name" in b
        assert "relPath" in b
        assert "viewCount" in b
        assert "views" in b
        assert "formulas" in b
        assert "properties" in b
        assert "rawYaml" in b


def test_obsidian_canvas_post(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test POST /api/obsidian/canvas procedural JSON Canvas 1.0 synthesis."""
    _, base_url, _ = obsidian_server

    # Validation check: empty topic returns 400
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        _http_post(f"{base_url}/api/obsidian/canvas", {"topic": ""})
    assert exc_info.value.code == 400

    # Successful canvas generation
    test_topic = "Wave11 Pytest Cluster"
    status, _, body = _http_post(f"{base_url}/api/obsidian/canvas", {"topic": test_topic})
    assert status == 201
    data = json.loads(body.decode("utf-8"))
    assert data["ok"] is True
    assert "canvas" in data
    canvas = data["canvas"]
    assert "name" in canvas
    assert "relPath" in canvas
    assert canvas["nodeCount"] >= 1
    assert "nodes" in canvas
    assert "edges" in canvas

    # Cleanup generated canvas file
    vault_dir = Path.home() / "Documents" / "Obsidian Vault"
    gen_file = vault_dir / canvas["name"]
    if gen_file.exists():
        try:
            gen_file.unlink()
        except Exception:
            pass


def test_obsidian_ingest_post(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test POST /api/obsidian/ingest creates Markdown note and stores STDP engram."""
    _, base_url, daemon = obsidian_server

    # Validation check: missing title/content returns 400
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        _http_post(f"{base_url}/api/obsidian/ingest", {"title": "", "content": ""})
    assert exc_info.value.code == 400

    # Successful ingestion
    test_payload = {
        "title": "Wave 11 Pytest Ingestion Spec",
        "content": "Autonomous agents require zero-trust cryptographically verified supply chain boundaries.",
        "source": "pytest-unit-test",
        "tags": ["agents", "zero-trust", "pytest"]
    }
    status, _, body = _http_post(f"{base_url}/api/obsidian/ingest", test_payload)
    assert status == 201
    data = json.loads(body.decode("utf-8"))
    assert data["ok"] is True
    assert "note" in data
    note = data["note"]
    assert note["title"] == "Wave 11 Pytest Ingestion Spec"
    assert "slug" in note
    assert "relPath" in note
    assert "memoryId" in note

    # Verify physical file was written with YAML frontmatter
    vault_dir = Path.home() / "Documents" / "Obsidian Vault"
    ingested_file = vault_dir / note["relPath"]
    assert ingested_file.exists()
    content_text = ingested_file.read_text(encoding="utf-8")
    assert "---" in content_text
    assert "title: \"Wave 11 Pytest Ingestion Spec\"" in content_text
    assert "[[00 Home]]" in content_text

    # Cleanup test file
    try:
        ingested_file.unlink()
    except Exception:
        pass


def test_obsidian_search_get(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test GET /api/obsidian/search returns unified vault and STDP matches."""
    _, base_url, daemon = obsidian_server

    # Seed an STDP engram into the test daemon
    daemon.store(
        text="Vaelor PoUW consensus mechanism secures autonomous agent swarm payments.",
        tags=["vaelor", "pouw", "consensus"],
        importance=0.95,
        category="semantic"
    )

    # Empty search query
    status, _, body = _http_get(f"{base_url}/api/obsidian/search?q=")
    assert status == 200
    empty_data = json.loads(body.decode("utf-8"))
    assert empty_data["ok"] is True
    assert empty_data["vaultCount"] == 0
    assert empty_data["stdpCount"] == 0

    # Search for "Vaelor"
    status, _, body = _http_get(f"{base_url}/api/obsidian/search?q=Vaelor")
    assert status == 200
    data = json.loads(body.decode("utf-8"))
    assert data["ok"] is True
    assert data["query"] == "Vaelor"
    assert data["vaultCount"] > 0
    assert "vaultMatches" in data
    assert "stdpMatches" in data
    assert data["stdpCount"] > 0

    first_vm = data["vaultMatches"][0]
    assert "title" in first_vm
    assert "relPath" in first_vm
    assert "type" in first_vm
    assert "snippet" in first_vm
    assert "wikilinks" in first_vm

    first_sm = data["stdpMatches"][0]
    assert "id" in first_sm
    assert "content" in first_sm
    assert "importance" in first_sm
    assert "category" in first_sm
    assert "tags" in first_sm
    assert "Vaelor" in first_sm["content"] or "vaelor" in [t.lower() for t in first_sm["tags"]]


def test_obsidian_search_post(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test POST /api/obsidian/search returns unified search results."""
    _, base_url, daemon = obsidian_server

    daemon.store(
        text="Hermes agent fleet synchronizes cognitive context across ZothOS nodes.",
        tags=["hermes", "fleet", "zothos"],
        importance=0.88,
        category="episodic"
    )

    status, _, body = _http_post(f"{base_url}/api/obsidian/search", {"query": "Hermes"})
    assert status == 200
    data = json.loads(body.decode("utf-8"))
    assert data["ok"] is True
    assert data["query"] == "Hermes"
    assert "vaultMatches" in data
    assert "stdpMatches" in data
    assert data["stdpCount"] > 0
    assert any("Hermes" in sm["content"] for sm in data["stdpMatches"])


def test_obsidian_telemetry_get(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test GET /api/obsidian/telemetry returns compiled telemetry markdown notes."""
    _, base_url, _ = obsidian_server
    status, _, body = _http_get(f"{base_url}/api/obsidian/telemetry")
    assert status == 200
    data = json.loads(body.decode("utf-8"))
    assert data["ok"] is True
    assert "count" in data
    assert "notes" in data
    assert data["count"] >= 3
    titles = [n["title"] for n in data["notes"]]
    assert any("Neuro-Memory" in t for t in titles)
    assert any("Vaelor" in t for t in titles)
    first_note = data["notes"][0]
    assert "relPath" in first_note
    assert "updated" in first_note
    assert "content" in first_note
    assert "---" in first_note["content"]


def test_obsidian_render_post(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test POST /api/obsidian/render invokes Knap telemetry compilation."""
    _, base_url, _ = obsidian_server
    status, _, body = _http_post(f"{base_url}/api/obsidian/render", {"target": "all"})
    assert status == 200
    data = json.loads(body.decode("utf-8"))
    assert data["ok"] is True
    assert data["target"] == "all"
    assert "notes" in data
    assert data["count"] >= 3
    titles = [n["title"] for n in data["notes"]]
    assert any("Neuro-Memory" in t for t in titles)


def test_obsidian_graph_get(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test GET /api/obsidian/graph returns vault degree centrality and top hubs."""
    _, base_url, _ = obsidian_server
    status, _, body = _http_get(f"{base_url}/api/obsidian/graph")
    assert status == 200
    data = json.loads(body.decode("utf-8"))
    assert data["ok"] is True
    assert "totalNodes" in data
    assert "totalEdges" in data
    assert "clusters" in data
    assert "topHubs" in data
    assert data["totalNodes"] >= 1600
    assert data["totalEdges"] >= 5000
    assert len(data["topHubs"]) >= 10
    first_hub = data["topHubs"][0]
    assert "title" in first_hub
    assert "relPath" in first_hub
    assert "inDegree" in first_hub
    assert "outDegree" in first_hub
    assert "totalDegree" in first_hub
    assert "cluster" in first_hub
    assert first_hub["totalDegree"] >= first_hub["inDegree"]


def test_mcp_obsidian_vault_search(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test MCP tool obsidian_vault_search via JSON-RPC."""
    _, _, daemon = obsidian_server
    mcp = MCPServer(daemon=daemon)
    assert "obsidian_vault_search" in mcp.tools

    req = {
        "jsonrpc": "2.0",
        "id": 101,
        "method": "tools/call",
        "params": {
            "name": "obsidian_vault_search",
            "arguments": {"query": "Vaelor", "limit": 5}
        }
    }
    resp = mcp.handle_request(req)
    assert resp is not None
    assert not resp["result"].get("isError", False)
    content = json.loads(resp["result"]["content"][0]["text"])
    assert content["ok"] is True
    assert content["query"] == "Vaelor"
    assert content["vaultCount"] > 0
    assert "vaultMatches" in content


def test_mcp_obsidian_wiki_synthesize(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test MCP tool obsidian_wiki_synthesize via JSON-RPC."""
    _, _, daemon = obsidian_server
    mcp = MCPServer(daemon=daemon)
    assert "obsidian_wiki_synthesize" in mcp.tools

    req = {
        "jsonrpc": "2.0",
        "id": 102,
        "method": "tools/call",
        "params": {
            "name": "obsidian_wiki_synthesize",
            "arguments": {"topic": "Vaelor Account-Lattice & PoUW Protocol"}
        }
    }
    resp = mcp.handle_request(req)
    assert resp is not None
    assert not resp["result"].get("isError", False)
    content = json.loads(resp["result"]["content"][0]["text"])
    assert content["ok"] is True
    assert content["status"] == "synthesized"
    assert "Vaelor" in content["article"]["title"]


def test_mcp_obsidian_canvas_generate(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test MCP tool obsidian_canvas_generate via JSON-RPC."""
    _, _, daemon = obsidian_server
    mcp = MCPServer(daemon=daemon)
    assert "obsidian_canvas_generate" in mcp.tools

    req = {
        "jsonrpc": "2.0",
        "id": 103,
        "method": "tools/call",
        "params": {
            "name": "obsidian_canvas_generate",
            "arguments": {"topic": "Wave 16 MCP Test Canvas"}
        }
    }
    resp = mcp.handle_request(req)
    assert resp is not None
    assert not resp["result"].get("isError", False)
    content = json.loads(resp["result"]["content"][0]["text"])
    assert content["ok"] is True
    assert "canvas" in content
    canvas = content["canvas"]
    assert canvas["nodeCount"] >= 3
    assert canvas["edgeCount"] >= 2

    # Cleanup generated canvas file
    vault_dir = Path.home() / "Documents" / "Obsidian Vault"
    canvas_file = vault_dir / canvas["name"]
    try:
        if canvas_file.exists():
            canvas_file.unlink()
    except Exception:
        pass


def test_mcp_obsidian_doctor_audit(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test MCP tool obsidian_doctor_audit via JSON-RPC."""
    _, _, daemon = obsidian_server
    mcp = MCPServer(daemon=daemon)
    assert "obsidian_doctor_audit" in mcp.tools

    req = {
        "jsonrpc": "2.0",
        "id": 104,
        "method": "tools/call",
        "params": {
            "name": "obsidian_doctor_audit",
            "arguments": {}
        }
    }
    resp = mcp.handle_request(req)
    assert resp is not None
    assert not resp["result"].get("isError", False)
    content = json.loads(resp["result"]["content"][0]["text"])
    assert content["ok"] is True
    assert content["score"] == 100
    assert content["healthGrade"] == "✦ PERFECT"
    assert content["totalCanvases"] >= 14
    assert content["totalBases"] >= 18
    assert "topHubs" in content


def test_api_mcp_tools_get(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test GET /api/mcp/tools returns list of 16 registered tools."""
    _, base_url, _ = obsidian_server
    status, _, body = _http_get(f"{base_url}/api/mcp/tools")
    assert status == 200
    data = json.loads(body.decode("utf-8"))
    assert data["ok"] is True
    assert data["count"] == 16
    assert len(data["tools"]) == 16
    tool_names = [t["name"] for t in data["tools"]]
    assert "obsidian_doctor_audit" in tool_names
    assert "obsidian_vault_search" in tool_names
    assert "obsidian_wiki_synthesize" in tool_names
    assert "obsidian_canvas_generate" in tool_names
    assert "obsidian_daily_log" in tool_names
    assert "memory_store" in tool_names
    assert "memory_recall" in tool_names


def test_api_mcp_call_post(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test POST /api/mcp/call invokes registered MCP tools and handles errors."""
    _, base_url, _ = obsidian_server

    # 1. Successful execution of obsidian_doctor_audit
    status, _, body = _http_post(f"{base_url}/api/mcp/call", {
        "name": "obsidian_doctor_audit",
        "arguments": {}
    })
    assert status == 200
    data = json.loads(body.decode("utf-8"))
    assert data["ok"] is True
    assert data["tool"] == "obsidian_doctor_audit"
    assert "result" in data
    assert data["result"]["ok"] is True
    assert data["result"]["score"] == 100
    assert data["result"]["healthGrade"] == "✦ PERFECT"

    # 2. Execution of memory_stats
    status, _, body = _http_post(f"{base_url}/api/mcp/call", {
        "name": "memory_stats",
        "arguments": {}
    })
    assert status == 200
    stats_data = json.loads(body.decode("utf-8"))
    assert stats_data["ok"] is True
    assert stats_data["tool"] == "memory_stats"

    # 3. Validation error: missing 'name' returns 400
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        _http_post(f"{base_url}/api/mcp/call", {"arguments": {}})
    assert exc_info.value.code == 400

    # 4. Unknown tool returns 404
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        _http_post(f"{base_url}/api/mcp/call", {"name": "nonexistent_mcp_tool"})
    assert exc_info.value.code == 404


def test_obsidian_bases_records_get(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test GET /api/obsidian/bases/records returns parsed base records."""
    _, base_url, _ = obsidian_server

    # 1. Query Zoth 71 Sovereign Tools.base
    status, _, body = _http_get(f"{base_url}/api/obsidian/bases/records?name=Zoth%2071%20Sovereign%20Tools.base")
    assert status == 200
    data = json.loads(body.decode("utf-8"))
    assert data["ok"] is True
    assert data["baseName"] == "Zoth 71 Sovereign Tools.base"
    assert data["totalMatched"] == 71
    assert len(data["columns"]) >= 5
    assert len(data["rows"]) == 71
    first_row = data["rows"][0]
    assert "title" in first_row
    assert "relPath" in first_row
    assert "properties" in first_row
    props = first_row["properties"]
    assert "file.name" in props
    assert "pillar" in props or "category" in props
    assert "formula.status_badge" in props

    # 2. Query Zoth LLM Wiki Index.base
    status, _, body = _http_get(f"{base_url}/api/obsidian/bases/records?name=Zoth%20LLM%20Wiki%20Index.base")
    assert status == 200
    wiki_data = json.loads(body.decode("utf-8"))
    assert wiki_data["ok"] is True
    assert wiki_data["totalMatched"] == 10
    assert len(wiki_data["rows"]) == 10

    # 3. Query without name defaults to tools
    status, _, body = _http_get(f"{base_url}/api/obsidian/bases/records")
    assert status == 200
    default_data = json.loads(body.decode("utf-8"))
    assert default_data["ok"] is True
    assert default_data["totalMatched"] == 71


def test_obsidian_daily_get(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test GET /api/obsidian/daily returns today's Daily Sovereign Note."""
    _, base_url, _ = obsidian_server
    status, _, body = _http_get(f"{base_url}/api/obsidian/daily")
    assert status == 200
    data = json.loads(body.decode("utf-8"))
    assert data["ok"] is True
    assert "date" in data
    assert "relPath" in data
    assert "07-Daily" in data["relPath"]
    assert "content" in data
    assert "Daily Sovereign Note" in data["content"]
    assert "Live Sovereign Snapshot" in data["content"]
    assert "entriesCount" in data
    assert data["entriesCount"] >= 1


def test_obsidian_daily_post(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test POST /api/obsidian/daily appends an engineering log entry and STDP engram."""
    _, base_url, daemon = obsidian_server

    # 1. Successful append
    status, _, body = _http_post(f"{base_url}/api/obsidian/daily", {
        "entry": "Automated pytest engineering log verification."
    })
    assert status == 201
    data = json.loads(body.decode("utf-8"))
    assert data["ok"] is True
    assert "Automated pytest engineering log verification." in data["content"]
    assert "appended" in data
    assert "Automated pytest engineering log verification." in data["appended"]
    assert data["entriesCount"] >= 2

    # 2. Validation error: missing entry returns 400
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        _http_post(f"{base_url}/api/obsidian/daily", {"entry": "  "})
    assert exc_info.value.code == 400


def test_mcp_obsidian_daily_log(obsidian_server: tuple[MemoryUIServer, str, MemoryDaemon]):
    """Test obsidian_daily_log MCP tool via direct JSON-RPC and HTTP API."""
    _, base_url, daemon = obsidian_server
    mcp = MCPServer(daemon=daemon)
    assert "obsidian_daily_log" in mcp.tools

    # 1. Direct MCP JSON-RPC call without entry (retrieval)
    req = {
        "jsonrpc": "2.0",
        "id": 201,
        "method": "tools/call",
        "params": {
            "name": "obsidian_daily_log",
            "arguments": {}
        }
    }
    resp = mcp.handle_request(req)
    assert resp is not None
    assert not resp["result"].get("isError", False)
    content = json.loads(resp["result"]["content"][0]["text"])
    assert content["ok"] is True
    assert "date" in content
    assert "relPath" in content
    assert "07-Daily" in content["relPath"]
    assert "Daily Sovereign Note" in content["content"]
    assert "Live Sovereign Snapshot" in content["content"]
    assert content["entriesCount"] >= 1

    # 2. Direct MCP JSON-RPC call with entry (append + STDP memory store)
    req2 = {
        "jsonrpc": "2.0",
        "id": 202,
        "method": "tools/call",
        "params": {
            "name": "obsidian_daily_log",
            "arguments": {
                "entry": "Synthesized Wave 20 Karpathy LLM Wiki articles & registered 16th MCP tool."
            }
        }
    }
    resp2 = mcp.handle_request(req2)
    assert resp2 is not None
    assert not resp2["result"].get("isError", False)
    content2 = json.loads(resp2["result"]["content"][0]["text"])
    assert content2["ok"] is True
    assert "Synthesized Wave 20 Karpathy LLM Wiki articles" in content2["content"]
    assert content2["entriesCount"] >= 2

    # Verify episodic STDP memory was recorded
    mem_matches = [
        m for m in daemon.nodes.values()
        if "Synthesized Wave 20 Karpathy LLM Wiki articles" in getattr(m, "text", "")
    ]
    assert len(mem_matches) >= 1
    assert "daily-note" in mem_matches[0].tags

    # 3. HTTP POST /api/mcp/call invocation
    status, _, body = _http_post(f"{base_url}/api/mcp/call", {
        "name": "obsidian_daily_log",
        "arguments": {
            "entry": "HTTP MCP tool invocation verification."
        }
    })
    assert status == 200
    http_data = json.loads(body.decode("utf-8"))
    assert http_data["ok"] is True
    assert http_data["tool"] == "obsidian_daily_log"
    assert "HTTP MCP tool invocation verification." in http_data["result"]["content"]










