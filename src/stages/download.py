import re
import time
from pathlib import Path
from urllib import request

from src.stages.stage import Stage


class Download(Stage):
    def __init__(
        self,
        save_path: Path,
        overwrite: bool = False,
        sleep: float = 1.,
        *args, **kwargs
    ):
        """
        Стадия скачивает файлы в save_path

        Parameters
        ----------
        save_path: Path | str
            Путь до папки сохранения файлов
        overwrite: bool
            Перезаписать файл, если он существует
        sleep: float
            Задержка между запросами
        """
        super().__init__(save_path=save_path, *args, **kwargs)

        self.overwrite = overwrite
        self.sleep = sleep

    def apply(self, file_id, file_name, link: str) -> Path:
        file_name = re.sub(r'[^\w\-_\. ]', '', str(file_name))
        file_name = f"({file_id}) {file_name}"
        file_path = self.save_path.joinpath(file_name)

        if file_path.exists() and not self.overwrite:
            return file_path

        _, msg = request.urlretrieve(link, file_path)

        time.sleep(self.sleep)

        return file_path
