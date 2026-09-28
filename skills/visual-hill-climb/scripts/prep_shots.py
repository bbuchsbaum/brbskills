"""Copy a complete lossless image set once; never replace recorded evidence."""
import argparse
import shutil
import sys
from common import child, config, identifier, image_files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('round')
    args = parser.parse_args()
    round_id = identifier(args.round)
    harness, cfg = config()
    files = image_files(harness, cfg, round_id, 'shots')
    destination = child(harness, 'artifact', 'img', round_id)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.mkdir()  # exclusive: existing rounds must not be overwritten
    for file in files:
        shutil.copyfile(file, destination / file.name)
    print(f'{round_id}: copied {len(files)} lossless PNGs to {destination}')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f'prep_shots: {error}', file=sys.stderr)
        sys.exit(1)
