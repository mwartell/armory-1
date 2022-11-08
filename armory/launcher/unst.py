from omegaconf import OmegaConf, DictConfig

# from hydra.core.config_store import ConfigStore
import hydra


@hydra.main(version_base=None, config_path="conf", config_name="cifar")
def main(exp: DictConfig) -> None:
    print(OmegaConf.to_yaml(exp))

    print(f"{exp.attack.module=}")
    print(f"{exp.attack.kwargs=}")
    print(f"{type(exp.attack.name)=}")


main()
