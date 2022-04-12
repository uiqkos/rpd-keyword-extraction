from abc import ABC, abstractmethod
from pathlib import Path
from typing import Union


class Stage(ABC):
    def __init__(
        self,
        save_path: Union[Path, str] = None,
        verbose: bool = False,
        collect_inputs=False,
        errors: str = 'ignore'
    ):
        self.save = bool(save_path)
        self.save_path = Path(save_path) if save_path is not None else None

        if self.save_path and self.save_path.suffix == '':
            self.save_path.mkdir(parents=True, exist_ok=True)

        self.verbose = verbose
        self.errors = errors
        self.collect_inputs = collect_inputs

    @abstractmethod
    def apply(self, *args, **kwargs):
        pass
