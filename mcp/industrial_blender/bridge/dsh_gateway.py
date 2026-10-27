"""Complete DSH HTTP *service* API bridge, not a DSH frontend port.

A single Codex MCP process exposes this facade. All 186 /plan operations are
addressed by name at runtime; engine and Blender addon remain original upstream
code checked out at the pinned Git commit during Windows installation.
"""
from __future__ import annotations

import hashlib
import time
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

BASE_DEFAULT = "http://127.0.0.1:9877"
# These are all supported DSH backend routes that the MCP can reach. Host UI
# endpoints requiring the DSH panel are documented separately.
GET_ROUTES = frozenset({
    "/doctor", "/health", "/status", "/commands", "/who", "/frame.png",
    "/host/scene-items", "/host/jobs", "/host/jobs/log",
    "/host/selection/latest",
})
POST_ROUTES = frozenset({
    "/act", "/cmd", "/loop", "/view", "/plan", "/headless", "/launch",
    "/lease", "/release", "/perf", "/opt", "/worker", "/job",
    "/txn", "/preset",
    "/host/selection", "/host/selection/consume",
})
IMAGE_ROUTES = frozenset({"/frame.png", "/view"})
READ_LIMIT = 16 * 1024 * 1024


class DshUnavailable(RuntimeError):
    pass


class DshCallError(RuntimeError):
    def __init__(self, status: int, detail: str):
        super().__init__(f"DSH backend HTTP {status}: {detail}")
        self.status = status
        self.detail = detail


def base_url() -> str:
    # No remote URL: upstream can execute arbitrary local Python and launch processes.
    raw = os.environ.get("INDUSTRIAL_DSH_URL", BASE_DEFAULT).rstrip("/")
    u = urllib.parse.urlsplit(raw)
    if u.scheme != "http" or u.hostname not in {"localhost", "127.0.0.1"} or u.port != 9877 or u.username or u.password or u.path or u.query or u.fragment:
        raise ValueError("仅允许本机 http://127.0.0.1:9877 DSH 执行后端")
    return raw


def parse_json(data: bytes) -> Any:
    """Handle JSON as well as streaming NDJSON heartbeats from long DSH jobs."""
    try:
        return json.loads(data)
    except json.JSONDecodeError:
        parsed = []
        for line in data.decode("utf-8", "replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                parsed.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        if parsed:
            # Preserve the final meaningful result; heartbeat frames have no result.
            for item in reversed(parsed):
                if isinstance(item, dict) and ("result" in item or "error" in item or "ok" in item or "jobId" in item):
                    return item
            return parsed[-1]
        raise ValueError("DSH 返回了无法解析的 JSON/NDJSON")


def request(route: str, payload: dict | None = None, *, timeout: int = 90,
            query: dict | None = None, binary: bool = False) -> Any:
    method = "POST" if payload is not None else "GET"
    allowed = POST_ROUTES if method == "POST" else GET_ROUTES
    if route not in allowed:
        raise ValueError(f"未批准的 DSH {method} 路由: {route}")
    if not 1 <= timeout <= 3600:
        raise ValueError("timeout 秒数必须在 1..3600")
    if query is not None:
        if not isinstance(query, dict) or len(query) > 16:
            raise ValueError("非法 query")
        for key, value in query.items():
            if not isinstance(key, str) or not isinstance(value, (str, int, float, bool)):
                raise ValueError("query 只允许简单标量")
    qs = ("?" + urllib.parse.urlencode(query)) if query else ""
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
    headers = {"Content-Type": "application/json"} if body is not None else {}
    req = urllib.request.Request(base_url() + route + qs, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as res:
            n = 0
            pieces = []
            while True:
                chunk = res.read(min(65536, READ_LIMIT + 1 - n))
                if not chunk:
                    break
                pieces.append(chunk)
                n += len(chunk)
                if n > READ_LIMIT:
                    raise ValueError("DSH 响应超过 16 MB；请缩小截图或收取后台作业结果文件")
            content = b"".join(pieces)
            ct = res.headers.get("content-type", "")
    except urllib.error.HTTPError as exc:
        raise DshCallError(exc.code, exc.read(2048).decode("utf-8", "replace")) from exc
    except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
        raise DshUnavailable(f"无法连接 DSH HTTP 后端 {BASE_DEFAULT}；检查 Node 后端与 Blender Bridge: {exc}") from exc
    if binary:
        if content[:8] != b"\x89PNG\r\n\x1a\n":
            raise ValueError(f"DSH 返回的不是 PNG（Content-Type={ct}）")
        return content
    if route in IMAGE_ROUTES and ("image/png" in ct or content[:8] == b"\x89PNG\r\n\x1a\n"):
        raise ValueError("这是 PNG 图像接口；请使用 blender_dsh_view_image 工具")
    return parse_json(content)


def route_call(route: str, payload: dict, timeout: int = 90) -> dict:
    try:
        if route not in POST_ROUTES:
            raise ValueError("必须使用已注册的 DSH 写路由")
        result = request(route, payload, timeout=timeout)
        ok = not (isinstance(result, dict) and result.get("ok") is False)
        # Upstream business verdict is passed through, never map HTTP 200 to success blindly.
        return {"transport": "OK", "upstream_ok": ok, "route": route, "data": result}
    except DshCallError as exc:
        return {"transport": "FAIL", "status": exc.status, "error": exc.detail, "route": route}
    except Exception as exc:
        return {"transport": "UNRESOLVED", "route": route, "error": str(exc)}


def discover_upstream(root: Path) -> dict:
    repo = root / "vendor" / "dsh-blender-plugin"
    required = ["runtime/server.mjs", "runtime/engine.mjs", "runtime/catalog.mjs", "addon/dsh_blender_bridge.py", "LICENSE"]
    missing = [name for name in required if not (repo / name).is_file()]
    return {"repo": str(repo), "source_present": not missing, "missing": missing,
            "note": "DSH 源码由 Windows 安装器在此目录中克隆并固定版本；ZIP 不含整个上游仓库"}


def watch_frames(seconds:float=4.0,interval_ms:int=700,size:int=560)->dict:
    """Host-independent sampler approximating DSH rt_watch without DSH frontend UI."""
    if not (0.5<=seconds<=20) or not (200<=interval_ms<=5000) or not (120<=size<=1200):
        raise ValueError('watch 参数越界')
    frames=[]
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        t0=time.monotonic()
        png=request('/frame.png',query={'size':size},binary=True,timeout=40)
        frames.append({'elapsed_s':round(t0-(end-seconds),2),'sha256':hashlib.sha256(png).hexdigest(),'bytes':len(png)})
        next_time=t0+interval_ms/1000
        pause=min(next_time-time.monotonic(),end-time.monotonic())
        if pause>0:time.sleep(pause)
    return {'frames':frames,'unique_frames':len({f['sha256'] for f in frames}),
            'sampled':len(frames),'note':'这是 DSH 前端 watch 的无界面采样兼容实现；未保存所有完整帧。'}
