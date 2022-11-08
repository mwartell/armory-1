from dataclasses import dataclass

from omegaconf import OmegaConf, DictConfig

import hydra

# from armory import SRC_ROOT
# from hydra.core.config_store import ConfigStore


@dataclass
class Attack:
    module: str
    name: str
    use_label: bool
    knowledge: str = "white"
    kwargs: DictConfig = DictConfig({})


@dataclass
class Dataset:
    batch_size: int
    framework: str
    module: str
    name: str


@dataclass
class Scenario:
    module: str
    name: str
    kwargs: DictConfig = DictConfig({})


@dataclass
class Experiment:
    _description: str
    attack: Attack
    dataset: Dataset
    scenario: Scenario


@hydra.main(version_base=None, config_path="conf", config_name="cifar")
def main(exp: Experiment) -> None:
    print(OmegaConf.to_yaml(exp))

    print(f"{exp.attack.module=}")
    print(f"{exp.attack.kwargs=}")


main()
