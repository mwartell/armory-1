from typing import Optional
from dataclasses import dataclass
from pathlib import Path


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
