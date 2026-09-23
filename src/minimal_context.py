#!/usr/bin/env python3
"""Select a small dependency-aware source context from repo_index.json."""
from __future__ import annotations
import argparse,json
from pathlib import Path

def select(index:dict, query:str, max_bytes:int=30000)->list[dict]:
    terms=[t.lower() for t in query.replace("_"," ").split() if len(t)>1]
    scored=[]
    for f in index.get("files",[]):
        blob=(f.get("path","")+" "+" ".join(x.get("name","")+" "+x.get("summary","") for x in f.get("functions",[]))).lower()
        score=sum(blob.count(t) for t in terms)
        if score: scored.append((score,f))
    scored.sort(key=lambda x:(-x[0],x[1].get("bytes",0)))
    chosen=[]; used=0
    for score,f in scored:
        size=f.get("bytes",0)
        if chosen and used+size>max_bytes: continue
        chosen.append({"path":f["path"],"score":score,"bytes":size,"hash":f.get("hash"),"functions":f.get("functions",[])})
        used+=size
    return chosen

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("index",type=Path); ap.add_argument("query"); ap.add_argument("--max-bytes",type=int,default=30000)
    a=ap.parse_args(); idx=json.loads(a.index.read_text(encoding="utf-8"))
    print(json.dumps({"query":a.query,"selected":select(idx,a.query,a.max_bytes)},ensure_ascii=False,indent=2))
if __name__=="__main__": main()
