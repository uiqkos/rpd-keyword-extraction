import json
from functools import partial
from pathlib import Path
from typing import List, Tuple, Union

import camelot
import pandas as pd
from pikepdf import Pdf

from src.stages.stage import Stage


class ExtractTables(Stage):
    def __init__(self, overwrite: bool = True, *args, **kwargs):
        """
        Стадия извлекает таблицы из pdf документа.

        Parameters
        ----------
        overwrite: bool
            Перезаписать файл, если он существует
        save_path: Path | str
            Путь до папки сохранения. Таблицы сохраняются в файл {file_name}.tables.json
        """
        super().__init__(*args, **kwargs)
        self.overwrite = overwrite

    @staticmethod
    def _extract_tables(file_path) -> List[pd.DataFrame]:
        try:
            tables = camelot.read_pdf(str(file_path), pages='all')

        finally:
            pdf = Pdf.open(file_path, allow_overwriting_input=True)
            pdf.remove_unreferenced_resources()
            pdf.save()
            pdf.close()

            tables = camelot.read_pdf(str(file_path), pages='all')

        res = []

        for table in tables:
            df: pd.DataFrame = table.df
            df.columns = df.iloc[0]
            df.drop(0, axis=0, inplace=True)
            df = df.applymap(str)
            res.append(df)

        return res

    @staticmethod
    def _save_tables(file_path, tables):
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump({
                'tables': list(map(partial(
                    pd.DataFrame.to_dict, orient='split'
                ), tables))
            }, f, ensure_ascii=False)

    def apply(self, file_path: str) -> Union[Tuple[Union[Path, None], List[pd.DataFrame]], None]:
        """
        Извлекает таблицы из документа

        Parameters
        ----------
        file_path: str
            Путь до документа
        Returns
        -------
        Пару (путь, таблицы), где таблицы это список pd.DataFrame
        """
        try:
            tables = ExtractTables._extract_tables(file_path)

        except Exception as e:
            if self.errors == 'ignore':
                return
            raise e

        if self.save:
            new_file_path = self.save_path.joinpath(file_path.name + '.tables.json')

            if new_file_path.is_file() and not self.overwrite:
                return

            ExtractTables._save_tables(new_file_path, tables)

            return new_file_path, tables

        return None, tables
