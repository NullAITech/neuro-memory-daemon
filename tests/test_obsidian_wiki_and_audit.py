"""Tests for Obsidian Second Brain Wiki, Audit, and Sync REST API endpoints."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Generator

import pytest

from neuro_memory_daemon import MemoryDaemon
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

