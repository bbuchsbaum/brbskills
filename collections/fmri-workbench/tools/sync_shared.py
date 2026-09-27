#!/usr/bin/env python3
"""Copy maintained shared resources into every self-contained skill; --check is read-only."""
import argparse, json, shutil
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
def sync(check=False):
    errors=[]
    sources=[p for p in (ROOT/'shared').rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    for skill in sorted((ROOT/'skills').iterdir()):
        if not (skill/'SKILL.md').is_file(): continue
        pairs=[(p,skill/p.relative_to(ROOT/'shared')) for p in sources]
        pairs.append((ROOT/'LICENSE',skill/'LICENSE'))
        for src,dst in pairs:
            if check:
                if not dst.is_file() or dst.read_bytes()!=src.read_bytes(): errors.append(str(dst.relative_to(ROOT)))
            else:
                dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
    return errors
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args()
    errors=sync(a.check);print(json.dumps({'ok':not errors,'out_of_sync':errors},indent=2));raise SystemExit(2 if errors else 0)
