import json
from functools import partial
from pathlib import Path
from typing import List, Tuple

import camelot
import pandas as pd
from pikepdf import Pdf

from src.stages.stage import Stage


class ExtractTables(Stage):
    def __init__(self, save_path=None, fix_pdf=True, overwrite=True, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fix_pdf = fix_pdf
        self.save_path = save_path
        self.save_path.mkdir(exist_ok=True)
        self.save = bool(save_path)
        self.overwrite = overwrite

    def _extract_tables(self, file_path) -> List[pd.DataFrame]:
        try:
            tables = camelot.read_pdf(str(file_path), pages='all')

        except Exception:
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

    def _save_tables(self, file_path, tables, overwrite=True):
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump({
                'tables': list(map(partial(
                    pd.DataFrame.to_dict, orient='split'
                ), tables))
            }, f, ensure_ascii=False)

    def _process_file_path(self, file_path):
        new_file_path = None

        if self.save:
            new_file_path = self.save_path.joinpath(file_path.name + '.tables.json')
            if new_file_path.is_file() and not self.overwrite:
                return

        try:
            tables = self._extract_tables(file_path)

        except Exception as e:
            if self.errors == 'ignore':
                return
            raise e

        if new_file_path:
            self._save_tables(new_file_path, tables)

        return new_file_path, tables

    def apply(self, file_path) -> Tuple[Path, List[pd.DataFrame]]:
        if res := self._process_file_path(file_path):
            return res
