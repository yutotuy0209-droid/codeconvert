#!/usr/bin/env python3
"""Compare repository indexes and report only changed/new/removed files."""
from __future__ import annotations
import argparse,json
from pathlib import Path
def compare(old,new):
    a={x["path"]:x for x in old.get("files",[])}; b={x["path"]:x for x in new.get("files",[])}
    return {
      "changed":[p for p in sorted(a.keys()&b.keys()) if a[p].get("hash")!=b[p].get("hash")],
      "added":sorted(b.keys()-a.keys()),"removed":sorted(a.keys()-b.keys()),
      "unchanged":[p for p in sorted(a.keys()&b.keys()) if a[p].get("hash")==b[p].get("hash")]
    }
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("old",type=Path); ap.add_argument("new",type=Path); a=ap.parse_args()
    print(json.dumps(compare(json.loads(a.old.read_text(encoding="utf-8")),json.loads(a.new.read_text(encoding="utf-8"))),indent=2))
if __name__=="__main__": main()
