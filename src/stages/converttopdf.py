import warnings
from pathlib import Path
from typing import Iterator, List

from src.stages.stage import Stage
from src.utils import convert_docx_to_pdf, convert_doc_to_docx, progressbar


class ConvertToPdf(Stage):
    def __init__(self, overwrite=False, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.overwrite = overwrite

    def apply(self, file_path) -> Path:
        if file_path.name.endswith('.doc'):
            file_path = convert_doc_to_docx(file_path, self.overwrite)

        if file_path.name.endswith('.docx'):
            file_path = convert_docx_to_pdf(file_path, self.overwrite)

        if file_path.name.lower().endswith('.pdf'):
            return file_path

        raise Exception('Unable to parse file: ' + str(file_path))
