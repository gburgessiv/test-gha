#!/usr/bin/env python3

from pathlib import Path
import yaml

def parse_rotation_yaml(file_path: Path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

def main():
    my_dir = Path(__file__).resolve().parent
    rotation_yaml_path = my_dir / "rotation.yaml"
    # Parse the YAML file
    rotation_data = parse_rotation_yaml(rotation_yaml_path)
    print("Rotation data parsed successfully:")
    print(rotation_data)

if __name__ == "__main__":
    main()