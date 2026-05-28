#!/usr/bin/env python3
import argparse
from pathlib import Path
from PIL import Image

# --- Defaults ---

_input_dir_default: Path = Path(__file__).parent / 'models' / 'aprilcube' / 'meshes' / 'tags_original'
_output_dir_default: Path = None
# _input_size: int = 8
_output_size_default: int = 512
_force_scale_default: bool = False


def _get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Generate high-resolution aprilcube tag textures on demand.'
    )
    parser.add_argument(
        '--input-dir',
        type=type(_input_dir_default),
        default=_input_dir_default,
        help='Directory containing the original aprilcube tag images',
    )
    parser.add_argument(
        '--output-dir',
        type=type(_input_dir_default),
        default=_output_dir_default,
        help='Directory where generated high-res textures are written',
    )
    parser.add_argument(
        '--output-size', 
        type=int, 
        default=_output_size_default, 
        help='Output texture size in pixels'
    )
    parser.add_argument(
        '--force', 
        action='store_true',
        help='Regenerate textures even if they already exist'
    )
    return parser


def scale_up_tags(
        input_dir = _input_dir_default,
        output_dir = _output_dir_default,
        output_size = _output_size_default,
        force = _force_scale_default,
) -> None:
    
    files = sorted(input_dir.glob('*.png'))

    if output_dir is None:
        output_dir = input_dir.parent / f'tags_scaled'

    if not files:
        raise FileNotFoundError(f'No tag images found in {input_dir}')

    if output_dir.exists() and not force:
        all_ok = True
        for source_path in files:
            target_path = output_dir / source_path.name
            if not target_path.exists():
                all_ok = False
                break
            with Image.open(target_path) as img:
                if img.size != (output_size, output_size):
                    all_ok = False
                    break
        if all_ok:
            print(f'Scaled tags alread exists. Use --force to force a regeneration.')
            return

    output_dir.mkdir(parents=True, exist_ok=True)

    if force: print(f'Generating all scaled tags ...', end='')
    else: print(f'Generating missing scaled tags ...', end='')
    for source_path in files:
        target_path = output_dir / source_path.name
        if target_path.exists() and target_path.stat().st_size > 0 and not force:
            with Image.open(target_path) as img:
                if img.size == (output_size, output_size):
                    continue

        img = Image.open(source_path)
        img = img.convert('RGBA')
        img = img.resize((output_size, output_size), resample=Image.NEAREST)
        img.save(target_path)
    print(f'done.')


def main() -> None:
    args = _get_parser().parse_args()

    scale_up_tags(
        args.input_dir, 
        args.output_dir, 
        args.output_size, 
        args.force
    )


if __name__ == '__main__':
    main()
