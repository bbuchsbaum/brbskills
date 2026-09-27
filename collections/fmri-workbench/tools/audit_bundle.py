#!/usr/bin/env python3
"""Offline structural audit. Does not substitute for native provider validation or R tests.
Development-only dependencies: PyYAML, jsonschema.
"""
import json,re,sys
from pathlib import Path
import yaml,jsonschema
from sync_shared import sync
ROOT=Path(__file__).resolve().parents[1]
def audit():
    errors=sync(True); stats=[]
    portable={'name','description','license','compatibility','metadata','allowed-tools'}
    for skill in sorted((ROOT/'skills').iterdir()):
        if not (skill/'SKILL.md').is_file():continue
        text=(skill/'SKILL.md').read_text(); parts=text.split('---',2)
        if len(parts)!=3:errors.append(f'{skill.name}: frontmatter');continue
        md=yaml.safe_load(parts[1]); body=parts[2]
        if md.get('name')!=skill.name or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',skill.name):errors.append(f'{skill.name}: name')
        if not isinstance(md.get('description'),str) or not 1<=len(md['description'])<=1024:errors.append(f'{skill.name}: description')
        if set(md)-portable:errors.append(f'{skill.name}: nonportable fields')
        if len(text.splitlines())>=500:errors.append(f'{skill.name}: too long')
        if any(not isinstance(v,str) for v in md.get('metadata',{}).values()):errors.append(f'{skill.name}: metadata must be strings')
        for path in skill.rglob('*.md'):
            for dest in re.findall(r'\[[^\]]*\]\(([^)]+)\)',path.read_text()):
                if '://' in dest or dest.startswith('#'):continue
                resolved=(path.parent/dest.split('#')[0]).resolve()
                if not resolved.is_relative_to(skill.resolve()) or not resolved.exists():errors.append(f'{path.relative_to(ROOT)}: broken/escaping link {dest}')
        agents=yaml.safe_load((skill/'agents/openai.yaml').read_text())
        if '$'+skill.name not in agents['interface']['default_prompt']:errors.append(f'{skill.name}: default prompt')
        stats.append({'skill':skill.name,'skill_lines':len(text.splitlines()),'body_words':len(body.split()),'description_characters':len(md['description'])})
    a=json.loads((ROOT/'plugin.json').read_text());b=json.loads((ROOT/'.claude-plugin/plugin.json').read_text())
    for field in ['name','version','description']:
        if a[field]!=b[field]:errors.append('Manifest mismatch: '+field)
    for path in (ROOT/'shared/schemas').glob('*.json'):jsonschema.Draft202012Validator.check_schema(json.loads(path.read_text()))
    return {'ok':not errors,'errors':errors,'skills':stats,'total_description_characters':sum(x['description_characters'] for x in stats),
            'note':'Words/characters are measured; no token count or provider latency benchmark is claimed.'}
if __name__=='__main__':
    out=audit();print(json.dumps(out,indent=2));raise SystemExit(0 if out['ok'] else 2)
