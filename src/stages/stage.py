from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterable, Tuple


class Stage(ABC):
    def __init__(
        self,
        save_path: Path = None,
        unpack_result=False,
        verbose: bool = False,
        collect_inputs=False,
        errors: str = 'ignore'
    ):
        self.save = bool(save_path)
        self.save_path = save_path

        if save_path and save_path.suffix == '':
            self.save_path.mkdir(parents=True, exist_ok=True)

        self.unpack_result = unpack_result
        self.verbose = verbose
        self.errors = errors
        self.collect_inputs = collect_inputs

    @abstractmethod
    def apply(self, *args, **kwargs):
        pass
