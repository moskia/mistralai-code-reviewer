import os, logging, base64, requests
from urllib.parse import urlparse
from fastapi import HTTPException
from app.config import (
    ALLOWED_EXTS, SECONDARY_EXTS, IGNORE_DIRS,
    MAX_FILE_BYTES, MAX_TOTAL_BYTES, MAX_FILES, PREVIEW_LINES, DEFAULT_REF
)

logger = logging.getLogger(__name__)
TOKEN = os.getenv("GITHUB_TOKEN")

def _headers():
    return {"Authorization": f"token {TOKEN}"} if TOKEN else {}

def _parse_repo(url: str):
    if not url.startswith("https://github.com/"):
        raise HTTPException(status_code=422, detail="Invalid GitHub URL")
    parts = urlparse(url).path.strip("/").split("/")
    if len(parts) < 2:
        raise HTTPException(status_code=422, detail="Invalid GitHub URL")
    owner, repo = parts[0], parts[1]
    ref = DEFAULT_REF
    if len(parts) >= 4 and parts[2] == "tree":
        ref = parts[3]
    return owner, repo, ref

def _is_ignored(path: str) -> bool:
    return any(path.startswith(d) for d in IGNORE_DIRS)

def _ext(path: str) -> str:
    i = path.rfind(".")
    return path[i:].lower() if i != -1 else ""

def fetch_repo_and_generate_message(repo_url: str) -> str:
    owner, repo, ref = _parse_repo(repo_url)

    # existence check
    meta = requests.get(f"https://api.github.com/repos/{owner}/{repo}", headers=_headers(), timeout=15)
    if meta.status_code == 404:
        raise HTTPException(status_code=404, detail="Repository not found")
    if meta.status_code == 403:
        raise HTTPException(status_code=429, detail="GitHub rate limit reached")
    meta.raise_for_status()

    # list tree
    r = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/git/trees/{ref}?recursive=1",
        headers=_headers(), timeout=30
    )
    if r.status_code in (403, 404):
        raise HTTPException(status_code=r.status_code, detail="Repo tree unavailable")
    r.raise_for_status()
    tree = r.json().get("tree", [])
    if not tree:
        raise HTTPException(status_code=204, detail="Repository empty")

    # filter candidates
    candidates = []
    for node in tree:
        if node.get("type") != "blob":
            continue
        path = node["path"]
        if _is_ignored(path):
            continue
        ext = _ext(path)
        if ext in ALLOWED_EXTS or ext in SECONDARY_EXTS:
            if node.get("size") and node["size"] > MAX_FILE_BYTES:
                continue
            candidates.append(node)

    if not candidates:
        return "# Repository Files\n*(no eligible files matched)*"

    # prioritize code
    code = [n for n in candidates if _ext(n["path"]) in ALLOWED_EXTS]
    meta_files = [n for n in candidates if _ext(n["path"]) in SECONDARY_EXTS]
    ordered = sorted(code, key=lambda n: n["path"]) + sorted(meta_files, key=lambda n: n["path"])

    # fetch previews
    total_bytes, included = 0, 0
    lines = ["# Repository Files"]
    session = requests.Session(); session.headers.update(_headers())

    for node in ordered:
        if included >= MAX_FILES or total_bytes >= MAX_TOTAL_BYTES:
            lines.append(f"\n*(truncated: {included} files, {total_bytes} bytes)*")
            break

        contents_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{node['path']}?ref={ref}"
        cr = session.get(contents_url, timeout=30)
        if cr.status_code in (403, 404):
            continue
        cr.raise_for_status()
        data = cr.json()
        size = data.get("size", 0)
        if size and size > MAX_FILE_BYTES:
            continue

        if data.get("encoding") == "base64" and "content" in data:
            content = base64.b64decode(data["content"]).decode("utf-8", errors="replace")
        else:
            if not data.get("download_url"):
                continue
            download = session.get(data["download_url"], timeout=30)
            download.raise_for_status()
            content = download.text

        byte_len = len(content.encode("utf-8"))
        total_bytes += byte_len
        included += 1
        preview = "\n".join(content.splitlines()[:PREVIEW_LINES])

        lines.append(f"- `{node['path']}` ({byte_len} bytes)")
        lines.append("```")
        lines.append(preview)
        lines.append("```")

    return "\n".join(lines)

