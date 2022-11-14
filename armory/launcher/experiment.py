from dataclasses import dataclass
from typing import List, Optional, Union

import hydra
from omegaconf import OmegaConf, DictConfig, ListConfig

# from armory import SRC_ROOT
# from hydra.core.config_store import ConfigStore

# TODO: there is only one AudioChannel bearing experiment, so this might be wider
@dataclass
class AudioChannel:
    attenuation: float
    delay: int
    pytorch: bool


# TODO: class Adhoc needs a proper definition for now it is a Dict[str, Any]
class Adhoc(DictConfig):
    pass


@dataclass
class Attack:
    knowledge: str
    module: str
    name: str
    targeted: bool
    type: str
    use_adversarial_trainer: bool
    use_label: bool
    sweep_params: DictConfig = DictConfig({})
    generate_kwargs: DictConfig = DictConfig({})
    kwargs: DictConfig = DictConfig({})
    targeted_labels: DictConfig = DictConfig({})


@dataclass
class Dataset:
    batch_size: int
    eval_split: str
    framework: str
    index: str
    max_frames: int
    modality: str
    pad_data: bool
    train_split: str


@dataclass
class Defense:
    module: str
    name: str
    type: str
    data_augmentation: DictConfig = DictConfig({})
    kwargs: DictConfig = DictConfig({})


@dataclass
class Metric:
    means: bool
    perturbation: Union[str, List[str]]
    record_metric_per_sample: bool
    task: List[str]


@dataclass
class Model:
    fit: bool
    fit_kwargs: dict
    model_kwargs: dict
    module: str
    weights_file: Optional[str]
    wrapper_kwargs: dict


@dataclass
class Scenario:
    export_batches: bool
    kwargs: dict
    module: str
    name: str
    tracked_classes: list


@dataclass
class Sysconfig:
    docker_image: str
    external_github_repo: Optional[str | List[str]]
    gpus: str
    local_repo_path: Optional[str | List[str]]
    num_eval_batches: int
    output_dir: Optional[str]
    output_filename: Optional[str]
    set_pythonhashseed: bool
    use_gpu: bool


@dataclass
class Experiment:
    _description: str
    adhoc: Adhoc
    attack: Attack
    dataset: Dataset
    defense: Defense
    metric: Metric
    model: Model
    scenario: Scenario
    sysconfig: Sysconfig


@hydra.main(version_base=None, config_path="conf", config_name="cifar10")
def main(exp: Experiment) -> None:
    print(OmegaConf.to_yaml(exp))

    print(f"{exp.attack.module=}")
    print(f"{exp.attack.kwargs=}")

    import yaml

    foo = yaml.load(open("armory/launcher/conf/cifar10.yaml"), Loader=yaml.FullLoader)
    assert OmegaConf.to_yaml(exp) == OmegaConf.to_yaml(foo)


main()
