#! /usr/bin/env python3
"""
Convert scenario configs from JSON to YAML experiments.

Hardcoded to draw from scenario_configs and create a parallel tree in experiments.
This will likely only be run once, but is kept around for reference.
"""


from pathlib import Path

from omegaconf import OmegaConf


sources = Path("scenario_configs").glob("**/*.json")
dest = Path("experiments")
dest.mkdir(exist_ok=True)

for source in sources:
    config = OmegaConf.load(source)
    experiment = OmegaConf.create(OmegaConf.to_yaml(config))

    # create a tree under dest parallel to the source tree
    yaml_dir = dest.joinpath(*source.parts[1:-1])
    yaml_dir.mkdir(parents=True, exist_ok=True)
    yaml_file = yaml_dir / source.with_suffix(".yml").name

    OmegaConf.save(experiment, yaml_file)
    print(f"wrote {yaml_file} from {source}")
