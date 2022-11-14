"""
Defines the Experiment class which holds all the configuration information
passed to armory engine.
"""

from dataclasses import dataclass
from typing import Any, List, Optional, Union

from omegaconf import OmegaConf

# TODO: there is only one AudioChannel bearing experiment, so this might be wider
@dataclass
class AudioChannel:
    attenuation: float
    delay: int
    pytorch: bool


@dataclass
class Adhoc:
    audio_channel: AudioChannel
    compute_fairness_metrics: bool
    experiment_id: int
    explanatory_model: Optional[str]
    fit_defense_classifier_outside_defense: bool
    fraction_poisoned: float
    poison_dataset: bool
    skip_adversarial: bool
    source_class: Union[int, List[int]]
    split_id: int
    target_class: Union[int, List[int]]
    train_epochs: int
    trigger_index: None
    use_poison_filtering_defense: bool


@dataclass
class Attack:
    generate_kwargs: dict
    knowledge: str
    kwargs: dict
    module: str
    name: str
    sweep_params: dict
    targeted_labels: dict
    targeted: bool
    type: str
    use_adversarial_trainer: bool
    use_label: bool


@dataclass
class Dataset:
    batch_size: int
    eval_split: str
    framework: str
    index: str
    max_frames: int
    module: str
    name: str
    modality: str
    pad_data: bool
    train_split: str


@dataclass
class Defense:
    data_augmentation: dict
    kwargs: dict
    module: str
    name: str
    type: str


@dataclass
class Metric:
    means: bool
    perturbation: Any
    record_metric_per_sample: bool
    task: List[str]


@dataclass
class Model:
    fit: bool
    fit_kwargs: dict
    model_kwargs: dict
    module: str
    name: str
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
    external_github_repo: Optional[List[str]]
    gpus: str
    local_repo_path: Optional[List[str]]
    num_eval_batches: int
    output_dir: Optional[str]
    output_filename: Optional[str]
    set_pythonhashseed: bool
    use_gpu: bool


@dataclass
class Experiment:
    _description: str
    adhoc: Optional[Adhoc]
    attack: Attack
    dataset: Dataset
    defense: Optional[Defense]
    metric: Metric
    model: Model
    scenario: Scenario
    sysconfig: Sysconfig


if __name__ == "__main__":
    from armory import SRC_ROOT
    from pprint import pprint

    empty = OmegaConf.structured(Experiment)
    print(f"{empty=}")

    cifar = SRC_ROOT.parent / "experiments/cifar10_baseline.yaml"
    assert cifar.exists()
    loaded = OmegaConf.load(cifar)

    merged = OmegaConf.merge(empty, loaded)
    print(OmegaConf.to_yaml(merged))

    missing = OmegaConf.missing_keys(merged)
    print(f"{missing=}")
