#!/usr/bin/env python3
"""Copy selected standalone skills into a Claude Code or Codex skill directory.
No downloads, dependency installs, global instructions, hooks or overwrites.
"""
import argparse,json,shutil,tempfile,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
NAMES=tuple(sorted(p.name for p in (ROOT/'skills').iterdir() if (p/'SKILL.md').is_file()))
def install(target,project=None,user=False,skills=None):
    if target not in ('claude','codex') or ((project is None)==(not user)):
        raise ValueError('Choose exactly one of project or user, and a supported target')
    names=list(skills or NAMES)
    if len(set(names))!=len(names) or any(n not in NAMES for n in names): raise ValueError('Unknown or duplicate skill')
    parent=(Path.home() if user else Path(project).expanduser().resolve())/('.claude' if target=='claude' else '.agents')/'skills'
    destinations=[parent/n for n in names]
    for n,dst in zip(names,destinations):
        if dst.exists() or dst.is_symlink(): raise ValueError(f'Refusing to overwrite {dst}')
        if any(p.is_symlink() for p in (ROOT/'skills'/n).rglob('*')): raise ValueError('Source symlinks are unsupported')
    parent.mkdir(parents=True,exist_ok=True)
    # Stage each copy; errors may leave earlier selected skills installed, never overwrite them.
    for n,dst in zip(names,destinations):
        stage=Path(tempfile.mkdtemp(prefix='.fmri-install-',dir=parent))
        try:
            shutil.copytree(ROOT/'skills'/n,stage/'payload',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
            # mkdir reserves the destination atomically against another installer.
            dst.mkdir()
            for child in (stage/'payload').iterdir(): shutil.move(str(child),str(dst/child.name))
        finally: shutil.rmtree(stage,ignore_errors=True)
    return [str(p) for p in destinations]
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--target',choices=['claude','codex'],required=True)
    g=p.add_mutually_exclusive_group(required=True);g.add_argument('--project',type=Path);g.add_argument('--user',action='store_true')
    p.add_argument('--skills',nargs='+',choices=NAMES);a=p.parse_args()
    try: print(json.dumps({'installed':install(a.target,a.project,a.user,a.skills)},indent=2));return 0
    except (ValueError,OSError) as e: print(json.dumps({'error':str(e)}));return 2
if __name__=='__main__':raise SystemExit(main())
