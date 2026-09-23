#!/usr/bin/env python3
"""Build a lightweight repository index for humans and AI agents."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from code_to_svg import analyze

SUPPORTED={".py",".cpp",".cc",".cxx",".c",".hpp",".hxx",".h",".m"}
SKIP={".git","node_modules",".venv","venv","build","dist","__pycache__",".ai"}

def digest(path: Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(65536),b""): h.update(chunk)
    return h.hexdigest()[:16]

def build_index(root: Path)->dict:
    files=[]
    for p in sorted(root.rglob("*")):
        if not p.is_file() or p.suffix.lower() not in SUPPORTED: continue
        if any(part in SKIP for part in p.relative_to(root).parts): continue
        try:
            funcs=analyze(p)
            files.append({
                "path":p.relative_to(root).as_posix(),
                "hash":digest(p),
                "bytes":p.stat().st_size,
                "functions":[{
                    "name":f.qualified_name,"lines":[f.lineno,f.end_lineno],
                    "calls":f.calls,"summary":f.doc[:160]
                } for f in funcs]
            })
        except Exception as e:
            files.append({"path":p.relative_to(root).as_posix(),"hash":digest(p),"bytes":p.stat().st_size,"error":str(e)})
    return {"version":1,"root":root.name,"files":files}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("root",type=Path); ap.add_argument("--out",type=Path,default=Path("repo_index.json"))
    a=ap.parse_args(); data=build_index(a.root.resolve())
    a.out.parent.mkdir(parents=True,exist_ok=True); a.out.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
if __name__=="__main__": main()
