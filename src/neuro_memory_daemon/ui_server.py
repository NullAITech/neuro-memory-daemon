"""Neural Memory Studio UI Server for neuro-memory-daemon.

Pure Python standard library implementation serving:
1. Material 3 Studio Web UI (`public/index.html`, design influenced by Material 3) with embedded fallback.
2. Complete REST API endpoints (/api/memories, /api/recall, /api/search,
   /api/graph, /api/consolidate, /api/stats, /api/health, /v1/memories/...).
3. Full CORS support for local web applications and AI agent runtimes.
Zero external dependencies.
"""

from __future__ import annotations

import json
import mimetypes
import os
import queue
import sys
import threading
import time
import urllib.parse
import webbrowser
import re
import subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from socketserver import ThreadingMixIn
from typing import Any, Dict, List, Optional, Union

from neuro_memory_daemon import (
    MemoryDaemon,
    __version__,
    get_default_daemon,
)
from neuro_memory_daemon.compat import normalize_path, safe_read_text
from neuro_memory_daemon.everywhere import collect as collect_everywhere
from neuro_memory_daemon.storage import StorageEngine, MemoryRecord
from neuro_memory_daemon.synapse_engine import SynapseEngine
from neuro_memory_daemon.graph_builder import GraphBuilder


def _safe_rel(raw: str) -> str:
    """Request path -> safe relative path inside a static dir; '' (index) if it
    tries to climb out with '..' or is absolute. Raw request paths are not normalised."""
    from urllib.parse import unquote
    rel = unquote(str(raw or "")).replace("\\", "/").lstrip("/")
    parts = [p for p in rel.split("/") if p not in ("", ".")]
    if any(p == ".." for p in parts) or ":" in (parts[0] if parts else ""):
        return ""
    return "/".join(parts)


def _parse_wiki_article(path: Path) -> Dict[str, Any]:
    """Parse Obsidian Flavored Markdown Wiki page with YAML frontmatter & callouts."""
    text = safe_read_text(path)
    title = path.stem
    created = ""
    updated = ""
    confidence = 0.99
    stdp_engrams = 0
    tags = []
    category = "LLM-Wiki"
    status = "CANONICAL"

    body = text
    fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.DOTALL)
    if fm_match:
        fm_text = fm_match.group(1)
        body = fm_match.group(2)
        for line in fm_text.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k == "title" and v:
                    title = v
                elif k == "created":
                    created = v
                elif k == "updated":
                    updated = v
                elif k == "confidence":
                    try:
                        confidence = float(v)
                    except ValueError:
                        pass
                elif k == "stdp_engrams":
                    try:
                        stdp_engrams = int(v)
                    except ValueError:
                        pass
                elif k == "status":
                    status = v
                elif k == "category":
                    category = v
                elif k == "tags":
                    tags = re.findall(r"[\w-]+", v)

    exec_summary = ""
    summary_match = re.search(r">\s*\[!abstract\]\s*(?:Executive Summary)?\s*\n((?:>.*\n?)+)", text)
    if summary_match:
        summary_raw = summary_match.group(1)
        exec_summary = "\n".join(re.sub(r"^>\s?", "", l) for l in summary_raw.splitlines()).strip()

    return {
        "title": title,
        "filename": path.name,
        "path": f"06-Wiki/{path.name}",
        "created": created,
        "updated": updated,
        "confidence": confidence,
        "stdp_engrams": stdp_engrams,
        "tags": tags,
        "category": category,
        "status": status,
        "executive_summary": exec_summary,
        "body": body.strip(),
        "size": path.stat().st_size if path.exists() else len(text.encode("utf-8")),
    }


class EventBroadcaster:
    """Thread-safe SSE event broadcaster for live agent/tool activity streaming."""

    def __init__(self) -> None:
        self._subscribers: List[queue.Queue] = []
        self._lock = threading.Lock()

    def subscribe(self) -> queue.Queue:
        q: queue.Queue = queue.Queue(maxsize=200)
        with self._lock:
            self._subscribers.append(q)
        return q

    def unsubscribe(self, q: queue.Queue) -> None:
        with self._lock:
            if q in self._subscribers:
                self._subscribers.remove(q)

    def broadcast(self, event_type: str, data: Any) -> None:
        event = {
            "type": event_type,
            "data": data,
            "timestamp": time.time(),
        }
        with self._lock:
            subscribers = list(self._subscribers)
        for q in subscribers:
            try:
                q.put_nowait(event)
            except queue.Full:
                pass


EVENT_BROADCASTER = EventBroadcaster()


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Multi-threaded HTTP server for non-blocking concurrent REST and UI requests."""

    daemon_threads = True
    allow_reuse_address = True


class StudioHTTPRequestHandler(BaseHTTPRequestHandler):
    """HTTP Request handler serving Material 3 Memory Studio and REST API."""

    server_daemon: Optional[MemoryDaemon] = None
    public_dir: Optional[Path] = None

    def _get_daemon(self) -> MemoryDaemon:
        if self.server_daemon is not None:
            return self.server_daemon
        return get_default_daemon()

    def _send_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")

    def _send_json(self, data: Any, status: int = 200) -> None:
        payload = json.dumps(data, indent=2, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self._send_cors_headers()
        self.end_headers()
        if not getattr(self, "_is_head", False):
            self.wfile.write(payload)

    def do_OPTIONS(self) -> None:
        """Handle CORS preflight requests."""
        self.send_response(204)
        self._send_cors_headers()
        self.end_headers()

    def do_HEAD(self) -> None:
        """Handle HEAD requests for static UI and REST API."""
        self._is_head = True
        try:
            self.do_GET()
        finally:
            self._is_head = False

    def do_GET(self) -> None:
        """Handle GET requests for static UI and REST API."""
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")
        if not path:
            path = "/"

        params = urllib.parse.parse_qs(parsed.query)

        # Health checks
        if path in ("/health", "/api/health", "/v1/health"):
            self._send_json({
                "status": "ok",
                "version": __version__,
                "service": "neuro-memory-daemon",
                "timestamp": time.time(),
            })
            return

        # Real-time Server-Sent Events (SSE) stream for 3D live trigger visuals
        if path in ("/api/stream", "/v1/stream"):
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self._send_cors_headers()
            self.end_headers()

            q = EVENT_BROADCASTER.subscribe()
            init_payload = json.dumps({"status": "connected", "service": "neuro-memory-daemon", "timestamp": time.time()})
            self.wfile.write(f"data: {init_payload}\n\n".encode("utf-8"))
            self.wfile.flush()

            try:
                while True:
                    try:
                        event = q.get(timeout=10.0)
                        msg = json.dumps(event, default=str)
                        self.wfile.write(f"data: {msg}\n\n".encode("utf-8"))
                        self.wfile.flush()
                    except queue.Empty:
                        self.wfile.write(b": ping\n\n")
                        self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError, OSError):
                pass
            finally:
                EVENT_BROADCASTER.unsubscribe(q)
            return

        daemon = self._get_daemon()

        # Telemetry & Stats
        if path in ("/api/stats", "/v1/memories/stats", "/v1/stats"):
            detailed = params.get("detailed", ["false"])[0].lower() in ("true", "1")
            stats = daemon.get_stats(detailed=detailed)
            self._send_json(stats)
            return

        if path in ("/api/diagnostics", "/v1/diagnostics"):
            verbose = params.get("verbose", ["false"])[0].lower() in ("true", "1")
            diag = daemon.diagnostics(verbose=verbose)
            self._send_json(diag)
            return

        # List memories
        if path in ("/api/memories", "/v1/memories"):
            # Check for query/search parameters
            q = params.get("q", [""])[0].strip()
            topic = params.get("topic", [""])[0].strip()
            cat = params.get("category", [""])[0].strip() or None
            tag = params.get("tag", [""])[0].strip() or None
            agent_id = params.get("agent_id", [""])[0].strip() or None
            limit = int(params.get("limit", ["100"])[0])

            if topic:
                results = daemon.recall(query=topic, top_k=limit, category=cat)
                self._send_json({"memories": results, "total": len(results)})
                return

            if q:
                results = daemon.search(query=q, category=cat, limit=limit, agent_id=agent_id)
                self._send_json({"memories": results, "total": len(results)})
                return

            # Return list of nodes with slice-before-serialize optimization
            raw_nodes = list(daemon.nodes.values())
            if cat:
                raw_nodes = [n for n in raw_nodes if getattr(n, "category", "") == cat]
            if agent_id:
                raw_nodes = [n for n in raw_nodes if getattr(n, "agent_id", "") == agent_id]
            if tag:
                tag_clean = tag.lower().lstrip("#")
                raw_nodes = [n for n in raw_nodes if tag_clean in [t.lower() for t in getattr(n, "tags", [])]]

            raw_nodes.sort(key=lambda x: getattr(x, "created_at", 0), reverse=True)
            nodes = [n.to_dict() for n in raw_nodes[:limit]]
            self._send_json({"memories": nodes, "total": len(daemon.nodes)})
            return

        # Specific memory by ID: /api/memories/<id> or /v1/memories/<id>
        if path.startswith("/api/memories/") or path.startswith("/v1/memories/"):
            parts = path.split("/")
            mem_id = parts[-1]
            if mem_id in daemon.nodes:
                self._send_json(daemon.nodes[mem_id].to_dict())
                return
            self._send_json({"error": "Memory not found", "id": mem_id}, status=404)
            return

        # Recall endpoint (GET with query param)
        if path in ("/api/recall", "/v1/memories/recall"):
            cue = params.get("query", [""])[0] or params.get("topic", [""])[0]
            top_k = int(params.get("top_k", ["5"])[0])
            min_score = float(params.get("min_score", ["0.1"])[0])
            cat = params.get("category", [""])[0] or None
            results = daemon.recall(query=cue, top_k=top_k, min_score=min_score, category=cat)
            self._send_json({"query": cue, "recalled": results, "count": len(results)})
            return

        # Search endpoint (GET)
        if path in ("/api/search", "/v1/search"):
            q = params.get("q", [""])[0] or params.get("query", [""])[0]
            cat = params.get("category", [""])[0] or None
            tag = params.get("tag", [""])[0] or None
            tags = [tag] if tag else None
            limit = int(params.get("limit", ["10"])[0])
            results = daemon.search(query=q, tags=tags, category=cat, limit=limit)
            self._send_json({"query": q, "results": results, "count": len(results)})
            return

        # Synaptic Graph
        if path in ("/api/graph", "/v1/memories/graph", "/v1/graph"):
            fmt = params.get("format", ["json"])[0].lower()
            min_weight = float(params.get("min_weight", ["0.05"])[0])
            node_limit = int(params.get("limit", ["50"])[0])
            root_id = params.get("root_id", [None])[0]

            graph_data = daemon.get_graph(
                format=fmt,
                min_weight=min_weight,
                node_limit=node_limit,
                root_id=root_id,
            )

            if fmt == "json" or isinstance(graph_data, dict):
                # Enrich with links format expected by frontend canvas
                if isinstance(graph_data, dict) and "edges" in graph_data and "links" not in graph_data:
                    graph_data["links"] = graph_data["edges"]
                self._send_json(graph_data)
            else:
                raw_bytes = str(graph_data).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Content-Length", str(len(raw_bytes)))
                self._send_cors_headers()
                self.end_headers()
                if not getattr(self, "_is_head", False):
                    self.wfile.write(raw_bytes)
            return

        elif path in ("/api/metacognition", "/v1/metacognition"):
            query = params.get("query", params.get("q", [""]))[0]
            top_k = int(params.get("top_k", [5])[0])
            res = daemon.audit_metacognition(query=query, top_k=top_k)
            self._send_json(res)
            return

        # Federated local memory ledger (Grok / Hermes / Zoth Bot / AGY + Neuro slice)
        if path in ("/api/everywhere", "/v1/everywhere"):
            source = params.get("source", [""])[0].strip()
            q = params.get("q", [""])[0].strip() or params.get("query", [""])[0].strip()
            include_archive = params.get("archive", ["false"])[0].lower() in ("true", "1", "yes")
            try:
                limit = int(params.get("limit", ["80"])[0])
            except (TypeError, ValueError):
                limit = 80
            payload = collect_everywhere(
                daemon=daemon,
                source=source,
                query=q,
                limit=limit,
                include_archive=include_archive,
            )
            self._send_json(payload)
            return

        # Neuromodulatory Status & Yerkes-Dodson Curve
        elif path in ("/api/neuromodulators", "/v1/neuromodulators", "/api/neuromodulator/status"):
            try:
                from .neuromodulation import get_default_neuromodulatory_system
            except ImportError:
                from neuro_memory_daemon.neuromodulation import get_default_neuromodulatory_system
            ns = get_default_neuromodulatory_system()
            comp_str = params.get("complexity", ["0.5"])[0]
            try:
                complexity = float(comp_str)
            except ValueError:
                complexity = 0.5
            status = ns.get_status()
            yd = ns.evaluate_yerkes_dodson(task_complexity=complexity)
            status["yerkes_dodson"] = yd.to_dict()
            self._send_json(status)
            return

        # Obsidian Second Brain & Official Skills Endpoint
        elif path in ("/api/obsidian/vault", "/v1/obsidian/vault"):
            vault_dir = Path.home() / "Documents" / "Obsidian Vault"
            notes = []
            canvases = []
            bases = []
            wikilink_edges = []
            import re as _re
            if vault_dir.exists():
                for p in sorted(vault_dir.rglob("*")):
                    if any(part.startswith(".") for part in p.parts) or not p.is_file():
                        continue
                    rel = str(p.relative_to(vault_dir))
                    if p.suffix.lower() == ".md":
                        txt = safe_read_text(p)
                        links = _re.findall(r"\[\[([^\]|#]+)", txt)
                        for target in links[:20]:
                            wikilink_edges.append({"from": p.stem, "to": target.strip()})
                        notes.append({
                            "name": p.stem,
                            "path": rel,
                            "size": p.stat().st_size,
                            "wikilinks": list(dict.fromkeys(l.strip() for l in links))[:15],
                            "isMoc": p.stem.startswith("MOC") or p.stem == "00 Home",
                        })
                    elif p.suffix.lower() == ".canvas":
                        canvases.append({"name": p.name, "path": rel, "size": p.stat().st_size})
                    elif p.suffix.lower() == ".base":
                        bases.append({"name": p.name, "path": rel, "size": p.stat().st_size})

            skills_list = [
                {"id": "obsidian-markdown", "name": "Obsidian Flavored Markdown", "author": "@kepano", "desc": "Wikilinks [[Note]], embeds ![[file]], callouts > [!tip], YAML properties & block IDs."},
                {"id": "json-canvas", "name": "JSON Canvas 1.0 (.canvas)", "author": "@kepano", "desc": "Spatial node & edge architecture boards, mind maps, and group containers."},
                {"id": "obsidian-bases", "name": "Obsidian Bases (.base)", "author": "@kepano", "desc": "Declarative YAML database tables, card galleries, filters & computed formulas."},
                {"id": "obsidian-cli", "name": "Obsidian CLI & URI Control", "author": "@kepano", "desc": "Live vault search, backlinks, daily notes, property mutation & plugin reload."},
                {"id": "knap", "name": "Knap Template Renderer", "author": "@kepano", "desc": "Turn structured JSON/CSV & STDP memory snapshots into formatted Markdown notes."},
                {"id": "defuddle", "name": "Defuddle Web Clipper", "author": "@kepano", "desc": "Zero-clutter web page to clean Obsidian Markdown extractor."},
                {"id": "obsidian-second-brain", "name": "Karpathy Second-Brain & STDP Bridge", "author": "NullAI", "desc": "Two-way sync between Obsidian Vault MOCs/Canvases and Neuro-Memory 3D STDP cortex."},
            ]
            self._send_json({
                "ok": True,
                "vaultPath": str(vault_dir),
                "noteCount": len(notes),
                "mocCount": sum(1 for n in notes if n["isMoc"]),
                "canvasCount": len(canvases),
                "baseCount": len(bases),
                "wikilinkEdgeCount": len(wikilink_edges),
                "skills": skills_list,
                "notes": notes[:60],
                "canvases": canvases,
                "bases": bases,
                "wikilinkEdges": wikilink_edges[:120],
            })
            return

        # Obsidian Karpathy LLM Wiki List Endpoint
        elif path in ("/api/obsidian/wiki", "/v1/obsidian/wiki"):
            vault_dir = Path.home() / "Documents" / "Obsidian Vault"
            wiki_dir = vault_dir / "06-Wiki"
            articles = []
            if wiki_dir.exists():
                for p in sorted(wiki_dir.glob("*.md")):
                    if not p.is_file() or p.name.startswith("."):
                        continue
                    articles.append(_parse_wiki_article(p))
            self._send_json({
                "ok": True,
                "count": len(articles),
                "articles": articles
            })
            return

        # Obsidian Second Brain Doctor Audit Endpoint
        elif path in ("/api/obsidian/audit", "/v1/obsidian/audit"):
            vault_dir = Path.home() / "Documents" / "Obsidian Vault"
            canvases = []
            bases = []
            notes = []
            total_wikilinks = 0
            connected_notes = 0
            canvas_valid = 0
            base_valid = 0

            if vault_dir.exists():
                for p in vault_dir.rglob("*"):
                    if any(part.startswith(".") for part in p.parts) or not p.is_file():
                        continue
                    if p.suffix.lower() == ".canvas":
                        canvases.append(p)
                        try:
                            cdata = json.loads(safe_read_text(p))
                            if isinstance(cdata, dict) and "nodes" in cdata and "edges" in cdata:
                                canvas_valid += 1
                        except Exception:
                            pass
                    elif p.suffix.lower() == ".base":
                        bases.append(p)
                        try:
                            import yaml
                            bdata = yaml.safe_load(safe_read_text(p))
                            if isinstance(bdata, dict) and "views" in bdata:
                                base_valid += 1
                        except Exception:
                            pass
                    elif p.suffix.lower() == ".md":
                        notes.append(p)
                        try:
                            txt = safe_read_text(p)
                            links = re.findall(r"\[\[([^\]|#]+)", txt)
                            if links:
                                connected_notes += 1
                                total_wikilinks += len(links)
                        except Exception:
                            pass

            wiki_files = list((vault_dir / "06-Wiki").glob("*.md")) if (vault_dir / "06-Wiki").exists() else []
            conn_pct = round((connected_notes / len(notes) * 100) if notes else 100.0, 1)
            score = 100
            if len(canvases) != canvas_valid:
                score -= min(10 * (len(canvases) - canvas_valid), 40)
            if len(bases) != base_valid:
                score -= min(10 * (len(bases) - base_valid), 40)

            self._send_json({
                "ok": True,
                "score": score,
                "status": "PERFECT" if score == 100 else "DEGRADED",
                "healthGrade": "✦ PERFECT" if score == 100 else "NEEDS_ATTENTION",
                "canvasesValid": canvas_valid,
                "totalCanvases": len(canvases),
                "basesValid": base_valid,
                "totalBases": len(bases),
                "totalNotes": len(notes),
                "totalWikilinks": total_wikilinks,
                "connectivityPct": conn_pct,
                "wikiCount": len(wiki_files),
            })
            return

        # Obsidian Second Brain Inventory & Full Status Endpoint
        elif path in ("/api/obsidian/status", "/v1/obsidian/status"):
            vault_dir = Path.home() / "Documents" / "Obsidian Vault"
            all_canvases = []
            all_bases = []
            wiki_articles = []
            total_notes = 0
            mocs = []
            if vault_dir.exists():
                for p in sorted(vault_dir.rglob("*")):
                    if any(part.startswith(".") for part in p.parts) or not p.is_file():
                        continue
                    if p.suffix.lower() == ".canvas":
                        all_canvases.append(p.name)
                    elif p.suffix.lower() == ".base":
                        all_bases.append(p.name)
                    elif p.suffix.lower() == ".md":
                        total_notes += 1
                        if p.stem.startswith("MOC") or p.stem == "00 Home":
                            mocs.append(p.stem)

            wiki_dir = vault_dir / "06-Wiki"
            if wiki_dir.exists():
                for wp in sorted(wiki_dir.glob("*.md")):
                    if wp.is_file() and not wp.name.startswith("."):
                        wiki_articles.append(wp.name)

            self._send_json({
                "ok": True,
                "vaultPath": str(vault_dir),
                "totalNotes": total_notes,
                "mocCount": len(mocs),
                "canvasCount": len(all_canvases),
                "baseCount": len(all_bases),
                "wikiCount": len(wiki_articles),
                "canvases": all_canvases,
                "bases": all_bases,
                "wikiArticles": wiki_articles,
            })
            return

        # Serve Static UI Files
        self._serve_static(path)

    def do_POST(self) -> None:
        """Handle POST requests for memory ingestion, recall, triggering, and consolidation."""
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")
        length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"

        try:
            body = json.loads(raw_body) if raw_body.strip() else {}
        except Exception:
            body = {}

        daemon = self._get_daemon()

        # Ingest / Store Memory
        if path in ("/api/memories", "/api/store", "/api/remember", "/v1/memories/encode", "/v1/memories"):
            text = body.get("text", "") or body.get("human_digest", "") or body.get("summary", "")
            if not text:
                self._send_json({"error": "Memory text is required"}, status=400)
                return

            res = daemon.store(
                text=text,
                tags=body.get("tags"),
                importance=float(body.get("importance", 0.5)),
                category=body.get("category", "episodic"),
                perspective=body.get("perspective", "first_person"),
                agent_id=body.get("agent_id", "default"),
                metadata=body.get("metadata") or body.get("raw_payload"),
            )
            EVENT_BROADCASTER.broadcast("memory_created", res)
            self._send_json({"status": "stored", "id": res["id"], "memory": res}, status=201)
            return

        # Associative Recall
        if path in ("/api/recall", "/v1/memories/recall"):
            cue = body.get("query", "") or body.get("topic", "") or body.get("cue", "")
            top_k = int(body.get("top_k", 5))
            min_score = float(body.get("min_score", 0.1))
            cat = body.get("category")
            spread_hops = int(body.get("spread_hops", 2))

            results = daemon.recall(
                query=cue,
                top_k=top_k,
                min_score=min_score,
                category=cat,
                spread_hops=spread_hops,
            )
            self._send_json({"query": cue, "recalled": results, "results": results, "count": len(results)})
            return

        # Filtered Search
        if path in ("/api/search", "/v1/search"):
            q = body.get("query", "") or body.get("q", "")
            tags = body.get("tags")
            cat = body.get("category")
            limit = int(body.get("limit", 10))
            agent_id = body.get("agent_id")

            results = daemon.search(
                query=q,
                tags=tags,
                category=cat,
                limit=limit,
                agent_id=agent_id,
            )
            self._send_json({"query": q, "results": results, "count": len(results)})
            return

        # Trigger / Spreading Activation / Action Potential
        if path in ("/api/trigger", "/v1/trigger") or "/trigger" in path:
            parts = path.split("/")
            url_mem_id = parts[-2] if len(parts) >= 3 and parts[-1] == "trigger" and parts[-2] not in ("api", "v1") else ""
            seed = body.get("seed") or body.get("id") or url_mem_id or body.get("cue") or ""
            text = body.get("text", "")
            tags = body.get("tags") or []
            category = body.get("category", "episodic")
            perspective = body.get("perspective", "agent")
            agent_id = body.get("agent_id", "default")
            decay = float(body.get("decay", 0.75))
            threshold = float(body.get("threshold", 0.1))
            max_hops = int(body.get("max_hops", 3))

            stored_mem = None
            if text:
                stored_mem = daemon.store(
                    text=text,
                    tags=tags,
                    importance=float(body.get("importance", 0.8)),
                    category=category,
                    perspective=perspective,
                    agent_id=agent_id,
                    metadata=body.get("metadata") or body.get("raw_payload"),
                )
                if not seed:
                    seed = stored_mem["id"]
                EVENT_BROADCASTER.broadcast("memory_created", stored_mem)

            if not seed and daemon.nodes:
                seed = next(iter(daemon.nodes.keys()))

            cascade = daemon.simulate_spreading_activation(
                seed=seed,
                decay=decay,
                threshold=threshold,
                max_hops=max_hops,
                auto_reinforce=True,
            )

            acc_count = 1
            if seed in daemon.nodes:
                daemon.nodes[seed].access_count += 1
                daemon.nodes[seed].last_accessed_at = time.time()
                acc_count = daemon.nodes[seed].access_count
                daemon._save()

            response_data = {
                "status": "triggered",
                "id": seed,
                "seed": seed,
                "access_count": acc_count,
                "last_accessed_at": time.time(),
                "cascade": cascade,
                "memory": stored_mem,
            }
            EVENT_BROADCASTER.broadcast("trigger", response_data)
            self._send_json(response_data, status=200)
            return

        # Link two memories
        if "/link" in path:
            parts = path.split("/")
            mem_id = parts[-2] if parts[-1] == "link" else ""
            target_id = body.get("target_id", "")
            weight = float(body.get("weight", 0.5))
            if mem_id in daemon.nodes and target_id in daemon.nodes:
                daemon.nodes[mem_id].synapses[target_id] = weight
                daemon.nodes[target_id].synapses[mem_id] = weight * 0.9
                daemon._save()
                self._send_json({"status": "linked", "source": mem_id, "target": target_id, "weight": weight})
                return
            self._send_json({"error": "Invalid memory IDs for link"}, status=400)
            return

        # Sleep Consolidation Pass
        if path in ("/api/consolidate", "/v1/memories/consolidate", "/v1/consolidate"):
            decay_rate = float(body.get("decay_rate", 0.05))
            prune_threshold = float(body.get("prune_threshold", 0.05))
            stdp_window = float(body.get("stdp_window", 3600.0))

            res = daemon.consolidate(
                decay_rate=decay_rate,
                prune_threshold=prune_threshold,
                stdp_window=stdp_window,
            )
            self._send_json({"status": "consolidated", **res})
            return

        # Metacognitive audit
        if path in ("/api/metacognition", "/v1/metacognition"):
            q = body.get("query", body.get("q", ""))
            top_k = int(body.get("top_k", 5))
            res = daemon.audit_metacognition(query=q, top_k=top_k)
            self._send_json(res)
            return

        # Neuromodulatory Pulse Injection
        if path in ("/api/neuromodulators/pulse", "/v1/neuromodulators/pulse"):
            try:
                from .neuromodulation import get_default_neuromodulatory_system
            except ImportError:
                from neuro_memory_daemon.neuromodulation import get_default_neuromodulatory_system
            ns = get_default_neuromodulatory_system()
            ne_d = float(body.get("ne_delta", 0.0))
            da_d = float(body.get("da_delta", 0.0))
            ach_d = float(body.get("ach_delta", 0.0))
            ser_d = float(body.get("serotonin_delta", 0.0))
            ns.pulse(ne_delta=ne_d, da_delta=da_d, ach_delta=ach_d, serotonin_delta=ser_d)
            status_data = ns.get_status()
            EVENT_BROADCASTER.broadcast("neuromodulator_pulse", status_data)
            self._send_json(status_data)
            return

        # Explicit Neuromodulator Levels Override
        if path in ("/api/neuromodulators/levels", "/v1/neuromodulators/levels"):
            try:
                from .neuromodulation import get_default_neuromodulatory_system
            except ImportError:
                from neuro_memory_daemon.neuromodulation import get_default_neuromodulatory_system
            ns = get_default_neuromodulatory_system()
            ns.set_levels(
                ne=body.get("norepinephrine"),
                da=body.get("dopamine"),
                ach=body.get("acetylcholine"),
                serotonin=body.get("serotonin"),
            )
            self._send_json(ns.get_status())
            return

        # Flashbulb Engram Permanent Consolidation
        if path in ("/api/neuromodulators/flashbulb", "/v1/neuromodulators/flashbulb", "/api/flashbulb"):
            mem_id = body.get("memory_id", "")
            if not mem_id:
                self._send_json({"error": "Field 'memory_id' is required for flashbulb tagging."}, status=400)
                return
            salience = float(body.get("salience", 1.0))
            reason = str(body.get("reason", "High-salience critical event"))
            res = daemon.tag_flashbulb(memory_id=mem_id, salience=salience, reason=reason)
            status_code = 200 if res.get("success") else 404
            self._send_json(res, status=status_code)
            return

        # Karpathy LLM Wiki Synthesis Endpoint
        if path in ("/api/obsidian/wiki", "/v1/obsidian/wiki"):
            topic = body.get("topic", "").strip()
            if not topic:
                self._send_json({"error": "Topic is required in JSON body: {\"topic\": \"...\"}"}, status=400)
                return

            cli_path = Path("/home/zoth/NullAITech/zoth-os/bin/zoth-second-brain")
            vault_dir = Path.home() / "Documents" / "Obsidian Vault"
            wiki_dir = vault_dir / "06-Wiki"
            wiki_dir.mkdir(parents=True, exist_ok=True)

            if cli_path.exists():
                try:
                    subprocess.run([str(cli_path), "wiki", topic], capture_output=True, text=True, timeout=25)
                except Exception:
                    pass

            clean_name = re.sub(r'["\']', '', topic).strip()
            target_file = wiki_dir / f"{clean_name}.md"
            if not target_file.exists():
                for p in wiki_dir.glob("*.md"):
                    if clean_name.lower() in p.stem.lower() or p.stem.lower() in clean_name.lower():
                        target_file = p
                        break

            if target_file.exists():
                article = _parse_wiki_article(target_file)
                daemon.store(
                    text=f"[Karpathy LLM Wiki · [[{article['title']}]]] {article['executive_summary'][:280]}",
                    tags=["wiki", "llm-wiki", "karpathy", article["title"].lower().replace(" ", "-")],
                    importance=0.96,
                    category="semantic",
                    agent_id="obsidian-bridge"
                )
                EVENT_BROADCASTER.broadcast("obsidian_wiki_synthesized", {"topic": topic, "file": target_file.name})
                self._send_json({
                    "ok": True,
                    "status": "synthesized",
                    "topic": topic,
                    "article": article
                }, status=201)
            else:
                self._send_json({"error": f"Failed to synthesize article for topic: {topic}"}, status=500)
            return

        # Two-Way Obsidian Second Brain <-> Neuro-Memory STDP Synchronization
        if path in ("/api/obsidian/sync", "/v1/obsidian/sync"):
            vault_dir = Path.home() / "Documents" / "Obsidian Vault"
            vault_dir.mkdir(parents=True, exist_ok=True)
            ingested = 0
            for moc_name in ("00 Home.md", "Zoth Memory.md", "Zoth Studio.md", "Zoth OS.md", "Vaelor Network.md", "MOC Skills.md", "MOC Daemons.md", "Zoth Trust & Supply Chain.md"):
                moc_file = vault_dir / moc_name
                if moc_file.exists():
                    snippet = safe_read_text(moc_file)[:280].replace("\n", " ").strip()
                    daemon.store(
                        text=f"[Obsidian Second Brain · [[{moc_file.stem}]]] {snippet}",
                        tags=["obsidian", "second-brain", "moc", moc_file.stem.lower().replace(" ", "-")],
                        importance=0.92,
                        category="semantic",
                        agent_id="obsidian-bridge",
                    )
                    ingested += 1
            for artifact_name in (
                "Zoth Second Brain.canvas",
                "Vaelor & Sovereign Economy.canvas",
                "Zoth Plugin & Connector Marketplace.canvas",
                "Zoth 6 Mathematical Pillars.canvas",
                "Zoth Autonomous Agents & Hermes Fleet.canvas",
                "Netrunner Cyber-Cortex Knowledge Map.canvas",
                "Zoth Memory Stratum.base",
                "Zoth Fleet & Daemons.base",
                "Zoth 71 Sovereign Tools.base",
                "Zoth Autonomous Agents.base",
                "Zoth LLM Wiki Index.base"
            ):
                art_file = vault_dir / artifact_name
                if art_file.exists():
                    snippet = safe_read_text(art_file)[:280].replace("\n", " ").strip()
                    daemon.store(
                        text=f"[Obsidian Second Brain · Spec Artifact {art_file.name}] {snippet}",
                        tags=["obsidian", "second-brain", "canvas" if art_file.suffix == ".canvas" else "base", art_file.stem.lower().replace(" ", "-")],
                        importance=0.90,
                        category="procedural",
                        agent_id="obsidian-bridge",
                    )
                    ingested += 1
            EVENT_BROADCASTER.broadcast("obsidian_synced", {"ingested": ingested, "vault": str(vault_dir)})
            all_canvases = sorted(p.name for p in vault_dir.glob("*.canvas"))
            all_bases = sorted(p.name for p in vault_dir.glob("*.base"))
            wiki_articles = sorted(p.name for p in (vault_dir / "06-Wiki").glob("*.md")) if (vault_dir / "06-Wiki").exists() else []
            self._send_json({
                "ok": True,
                "status": "synced",
                "ingestedFromVault": ingested,
                "totalMemories": len(daemon.nodes),
                "vaultPath": str(vault_dir),
                "canvases": all_canvases,
                "bases": all_bases,
                "wikiArticles": wiki_articles,
            })
            return

        self.send_error(404, f"API route not found: {path}")

    def do_DELETE(self) -> None:
        """Handle DELETE requests for pruning memory nodes."""
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")
        daemon = self._get_daemon()

        if path.startswith("/api/memories/") or path.startswith("/v1/memories/"):
            mem_id = path.split("/")[-1]
            if mem_id in daemon.nodes:
                deleted_node = daemon.nodes.pop(mem_id)
                # Remove dangling references
                for other in daemon.nodes.values():
                    other.synapses.pop(mem_id, None)
                daemon._save()
                self._send_json({"status": "deleted", "id": mem_id, "node": deleted_node.to_dict()})
                return
            self._send_json({"error": "Memory node not found", "id": mem_id}, status=404)
            return

        self.send_error(404, "Not Found")

    def _serve_static(self, req_path: str) -> None:
        """Serve files from public/ directory with embedded HTML fallback."""
        pub_dir = self.public_dir
        if pub_dir is None:
            # Look for public/ directory in project tree
            candidates = [
                Path(__file__).resolve().parent.parent.parent / "public",
                Path.cwd() / "public",
                Path.home() / ".neuro_memory" / "public",
            ]
            for c in candidates:
                if c.exists() and c.is_dir():
                    pub_dir = c
                    break

        if req_path in ("/", "/index.html"):
            index_file = pub_dir / "index.html" if pub_dir else None
            if index_file and index_file.exists():
                content = safe_read_text(index_file).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self._send_cors_headers()
                self.end_headers()
                if not getattr(self, "_is_head", False):
                    self.wfile.write(content)
                return

            # Fallback embedded Material 3 UI if public/index.html is missing
            self._serve_embedded_ui()
            return

        # Other static assets in public/
        if pub_dir:
            clean_rel = _safe_rel(req_path)
            target = pub_dir / clean_rel
            if target.exists() and target.is_file():
                mime_type, _ = mimetypes.guess_type(str(target))
                mime = mime_type or "application/octet-stream"
                data = target.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", mime)
                self.send_header("Content-Length", str(len(data)))
                self._send_cors_headers()
                self.end_headers()
                if not getattr(self, "_is_head", False):
                    self.wfile.write(data)
                return

        self.send_error(404, f"File Not Found: {req_path}")

    def _serve_embedded_ui(self) -> None:
        """Serve embedded single-file fallback UI."""
        fallback_html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Neural Memory Studio — Fallback</title>
  <style>
    body { font-family: -apple-system, sans-serif; background: #f1f3f4; color: #202124; padding: 40px; text-align: center; }
    .card { background: #fff; max-width: 600px; margin: 0 auto; padding: 30px; border-radius: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.12); }
    h1 { color: #1a73e8; }
    a { color: #1a73e8; font-weight: 600; text-decoration: none; }
  </style>
</head>
<body>
  <div class="card">
    <h1>🧠 Neural Memory Studio</h1>
    <p>Synaptic Daemon is running on <code>:8788</code></p>
    <p><a href="/api/stats">View Substrate Telemetry JSON</a></p>
  </div>
</body>
</html>"""
        data = fallback_html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self._send_cors_headers()
        self.end_headers()
        if not getattr(self, "_is_head", False):
            self.wfile.write(data)

    def log_message(self, format: str, *args: Any) -> None:
        """Suppress default HTTP logging for clean terminal output."""
        pass


class MemoryUIServer:
    """Manages the lifecycle of the Threaded Memory Studio UI and REST server."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8788,
        daemon: Optional[MemoryDaemon] = None,
        public_dir: Optional[Union[str, Path]] = None,
    ) -> None:
        self.host = host
        self.port = port
        self.daemon = daemon or get_default_daemon()
        self.public_dir = normalize_path(public_dir) if public_dir else None

        StudioHTTPRequestHandler.server_daemon = self.daemon
        StudioHTTPRequestHandler.public_dir = self.public_dir

        self.server = ThreadedHTTPServer((self.host, self.port), StudioHTTPRequestHandler)
        self._thread: Optional[threading.Thread] = None

    def start(self, in_thread: bool = False, open_browser: bool = False) -> None:
        """Start the HTTP server."""
        url = f"http://{self.host}:{self.port}"
        print(f"🚀 Neural Memory Studio (Material 3 influenced) running at {url}")

        # Auto-start live agent spooler
        try:
            from .spooler import start_spooler
            start_spooler(daemon=self.daemon)
        except Exception:
            pass

        if open_browser:
            webbrowser.open(url)

        if in_thread:
            self._thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self._thread.start()
        else:
            try:
                self.server.serve_forever()
            except KeyboardInterrupt:
                self.stop()

    def stop(self) -> None:
        """Shutdown the HTTP server."""
        self.server.shutdown()
        self.server.server_close()


def run_server(
    host: str = "127.0.0.1",
    port: int = 8788,
    open_browser: bool = False,
    daemon: Optional[MemoryDaemon] = None,
    db_path: Optional[Union[str, Path]] = None,
    public_dir: Optional[Union[str, Path]] = None,
) -> int:
    """Convenience functional runner for the UI server."""
    active_daemon = daemon or get_default_daemon(db_path=db_path)
    server = MemoryUIServer(
        host=host,
        port=port,
        daemon=active_daemon,
        public_dir=public_dir,
    )
    server.start(in_thread=False, open_browser=open_browser)
    return 0


def start_server_in_thread(
    host: str = "127.0.0.1",
    port: int = 8788,
    daemon: Optional[MemoryDaemon] = None,
    public_dir: Optional[Union[str, Path]] = None,
) -> MemoryUIServer:
    """Start UI server in background thread for testing or embedded use."""
    active_daemon = daemon or get_default_daemon()
    server = MemoryUIServer(
        host=host,
        port=port,
        daemon=active_daemon,
        public_dir=public_dir,
    )
    server.start(in_thread=True, open_browser=False)
    return server


if __name__ == "__main__":
    run_server(host="127.0.0.1", port=8788, open_browser=True)
