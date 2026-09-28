"""Validate completed critique tables and update the offline progress page.

Single writer only. Missing reviewers remain pending; malformed present reviews
fail before writes. Images must already be prepared unless --no-images is used.
"""
import argparse
import datetime
import json
import re
import sys
from common import atomic_text, child, config, identifier, image_files


def parse_scores(markdown, dims):
    sections = re.split(r'^##\s+Scores\s*$', markdown, flags=re.M | re.I)
    if len(sections) != 2:
        raise ValueError('Expected exactly one ## Scores section')
    section = re.split(r'^#{1,2}\s+', sections[1], maxsplit=1, flags=re.M)[0]
    rows, started = [], False
    for line in section.splitlines():
        if line.strip().startswith('|'):
            started = True
            rows.append([cell.strip().strip('*') for cell in line.strip().strip('|').split('|')])
        elif started:
            break
    if len(rows) < 3 or [x.lower() for x in rows[0][:2]] != ['dimension', 'score']:
        raise ValueError('Expected dimension / score table under ## Scores')
    if any(not re.fullmatch(r':?-{3,}:?', cell) for cell in rows[1]):
        raise ValueError('Invalid score table separator')
    scores = {}
    for row in rows[2:]:
        if len(row) < 2:
            raise ValueError('Malformed score row')
        dimension, value = row[:2]
        if dimension.lower() == 'mean':
            continue  # always recomputed, never trusted
        if dimension not in dims or dimension in scores:
            raise ValueError(f'Unknown or duplicate dimension: {dimension}')
        if not re.fullmatch(r'\d+(?:\.\d+)?', value) or not 1 <= float(value) <= 10:
            raise ValueError(f'Invalid score for {dimension}: {value}')
        scores[dimension] = float(value)
    if set(scores) != set(dims):
        raise ValueError(f'Missing score dimensions: {sorted(set(dims) - set(scores))}')
    return scores


def validate_critique(markdown, dims):
    scores = parse_scores(markdown, dims)
    required = ('Previous round', 'Claims', 'Issues', 'Regressions', 'Proposals')
    for heading in required:
        pieces = re.split(r'^##\s+' + re.escape(heading) + r'\s*$', markdown, flags=re.M | re.I)
        if len(pieces) != 2 or not re.split(r'^#{1,2}\s+', pieces[1], maxsplit=1, flags=re.M)[0].strip():
            raise ValueError(f'Incomplete critique: missing or empty {heading} section')
    return scores


def specimen_contract(cfg):
    shots = []
    for shot in cfg['shots']:
        capture = dict(shot)
        vp = capture.get('vp')
        if isinstance(vp, str):
            if vp not in cfg.get('viewports', {}):
                raise ValueError(f'Unknown viewport: {vp}')
            capture['vp'] = cfg['viewports'][vp]
        if 'file' in capture:
            capture.setdefault('dark', False)
            capture.setdefault('wait', 800)
        shots.append(capture)
    return shots


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('round')
    for name in ('title', 'summary', 'status', 'changes-file'):
        parser.add_argument('--' + name)
    parser.add_argument('--no-images', action='store_true')
    args = parser.parse_args()
    round_id = identifier(args.round)
    harness, cfg = config()
    artifact = child(harness, 'artifact')
    data_file = child(harness, 'artifact', 'data.json')
    data = json.loads(data_file.read_text(encoding='utf-8')) if data_file.exists() else {'rounds': []}
    contract = {key: cfg[key] for key in ('dims', 'critics')}
    contract['specimens'] = specimen_contract(cfg)
    shots = [{'id': s['name'], 'label': s.get('label', s['name'])} for s in cfg['shots']]
    if data['rounds'] and (data.get('contract') != contract or data.get('shots') != shots):
        raise ValueError('Rubric, critic roles or specimens changed; start a new baseline/harness')
    data['contract'] = contract
    data['meta'] = {key: cfg.get(key) for key in ('title', 'intro', 'dims', 'critics', 'captureNote')}
    data['shots'] = shots
    record = next((r for r in data['rounds'] if r['id'] == round_id), None)
    if record is None:
        record = {'id': round_id, 'title': round_id, 'date': str(datetime.date.today())}
        data['rounds'].append(record)
    for key in ('title', 'summary'):
        if getattr(args, key) is not None:
            record[key] = getattr(args, key)
    if args.changes_file:
        from pathlib import Path
        record['changes'] = [line.removeprefix('- ') for line in
                             Path(args.changes_file).read_text(encoding='utf-8').splitlines() if line.strip()]
    image_dir = child(harness, 'artifact', 'img', round_id)
    record['images'] = False
    if not args.no_images or image_dir.exists():
        image_files(harness, cfg, round_id, 'artifact/img')
        record['images'] = True
    record['scores'], record['critiques'] = {}, []
    copies = []
    for key, label in cfg['critics'].items():
        file = child(harness, 'critiques', f'{round_id}-{key}.md')
        if file.exists():
            markdown = file.read_text(encoding='utf-8')
            record['scores'][key] = validate_critique(markdown, cfg['dims'])
            target = child(harness, 'artifact', 'critiques', file.name)
            copies.append((target, markdown))
            record['critiques'].append({'critic': label, 'file': f'critiques/{file.name}', 'text': markdown})
    record['pending'] = [key for key in cfg['critics'] if key not in record['scores']]
    record['complete'] = not record['pending']
    if args.status is not None:
        data['status'] = args.status
    data.setdefault('status', 'Review pending')
    data['updated'] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    # Everything above is validated before any publication files are touched.
    for file, text in copies:
        atomic_text(file, text)
    payload = json.dumps(data, ensure_ascii=True, allow_nan=False, indent=2)
    atomic_text(data_file, payload + '\n')
    atomic_text(child(harness, 'artifact', 'data.js'), 'window.HILLCLIMB_DATA = ' + payload + ';\n')
    print(round_id, 'complete' if record['complete'] else 'pending: ' + ', '.join(record['pending']))


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f'update_data: {error}', file=sys.stderr)
        sys.exit(1)
