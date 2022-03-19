import os
import re
import time
from pathlib import Path
from typing import Iterator, List
from urllib import request

from src.stages.stage import Stage
from src.utils import progressbar


class Download(Stage):
    def __init__(
            self,
            overwrite=False,
            sleep: int = 1,
            *args,
            **kwargs
    ):
        super().__init__(*args, **kwargs)

        self.overwrite = overwrite
        self.sleep = sleep

    def apply(self, file_id, file_name, link) -> Path:
        file_name = re.sub(r'[^\w\-_\. ]', '', file_name)
        file_name = f"({file_id}) {file_name}"
        file_path = self.save_path.joinpath(file_name)

        if file_path.exists() and not self.overwrite:
            return file_path

        _, msg = request.urlretrieve(link, file_path)

        time.sleep(self.sleep)

        return file_path

