import pytest
import subprocess
import re
import os


def get_cmd_output(cmd):
    output = subprocess.check_output(cmd.split(" "))
    output = output.decode("utf-8")
    output = str(output).split("->")[1]
    output = output.replace("\n", "").strip()
    return output


@pytest.fixture
def armory_version_tbi():
    """Expected Version of Armory to be installed in Docker Image"""
    expected_armory_version = subprocess.check_output(
        "python setup.py --version".split(" ")
    )
    expected_armory_version = expected_armory_version.decode("utf-8")
    expected_armory_version = expected_armory_version.replace("\n", "").strip()
    return expected_armory_version


@pytest.fixture
def image_tag(armory_version_tbi):
    av = armory_version_tbi.replace("+", "-")
    tag = ".".join(av.split(".")[:-1])
    return tag


def get_short(value):
    return ".".join(value.split(".")[:-1])


@pytest.mark.parametrize(
    "img, opt",
    [
        ("base", ""),
        ("pytorch", ""),
        ("tf2", ""),
        ("pytorch-deepspeech", ""),
        ("base", "--no-cache"),
    ],
)
def test_build_script(img, opt, image_tag, armory_version_tbi):
    cmd = f"bash docker/build.sh -f {img} --dry-run {opt}"
    output = get_cmd_output(cmd)
    assert output.startswith("docker build")
    assert "--force-rm" in output

    if "--no-cache" in opt:
        assert "--no-cache" in output
    else:
        assert f"--cache-from twosixarmory/{img}:{image_tag}"

    docker_file = re.match(r"(.*?)--file\s+(.*?)\s+(.*?)", output).groups()[1]
    docker_file = os.path.basename(docker_file)

    assert docker_file == f"Dockerfile-{img}"

    if img != "base":
        base_img_tag = re.match(
            r"(.*?)--build-arg\s+base_image_tag=(.*?)\s+(.*?)", output
        ).groups()[1]
        assert base_img_tag == image_tag

        armory_version = re.match(
            r"(.*?)--build-arg\s+armory_version=(.*?)\s+(.*?)", output
        ).groups()[1]
        assert get_short(armory_version) == get_short(armory_version_tbi)

    image = re.match(r"(.*?)\s+-t\s+twosixarmory/(.*?)\s+", output).groups()[1]
    assert image == f"{img}:{image_tag}"