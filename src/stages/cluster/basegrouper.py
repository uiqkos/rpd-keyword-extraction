import json
from abc import ABC

from src.stages.stage import Stage


class BaseGrouper(Stage, ABC):
    def __init__(
        self,
        file_name: str = 'clusters.json',
        *args, **kwargs
    ):
        super().__init__(*args, **kwargs)

        self.file_name = file_name

    def _save_groups(self, groups, config: dict):
        if self.verbose:
            print(self.save_path.name)

        with open(self.save_path / self.file_name, 'w', encoding='utf-8') as file:
            json.dump({
                'params': config,
                'clusters': groups
            }, file, ensure_ascii=False, indent=4)
