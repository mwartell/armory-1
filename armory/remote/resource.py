from typing import Optional
from dataclasses import dataclass
from pathlib import Path

import requests
import boto3


@dataclass
class Authentication:
    base_url: str
    user: str
    password: str


@dataclass
class RemoteResource:
    url: str
    authentication: Optional[Authentication] = None

    def mount(self) -> Path:
        """Mounts the remote resource to a local store and returns its path."""
        raise NotImplementedError

    def unmount(self) -> None:
        """Unmounts the remote resource from the local store."""
        # TODO: not sure this will be needed, I expect mounts to be ephemeral.
        raise NotImplementedError
