import yaml
from omegaconf import OmegaConf

import armory.launcher.experiment
from armory import SRC_ROOT

REPO_ROOT = SRC_ROOT.parent


def test_roundtrip_yaml(experiments=REPO_ROOT.glob("experiments/**/*.yaml")):
    for experiment in experiments:
        text = experiment.read_text()
        omega = OmegaConf.create(text)
        config = yaml.safe_load(text)
        assert omega == config, f"{experiment} did not survive a roundtrip"
