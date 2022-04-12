from pathlib import Path
from typing import Union

import docx2pdf
from win32com import client as wc

from src.stages.stage import Stage


class ConvertToPdf(Stage):
    def __init__(self, overwrite: bool = False, *args, **kwargs):
        """
        Стадия конвертирует документы (.doc, .docx) в pdf

        Parameters
        ----------
        overwrite: bool
            Перезаписать файл, если он существует
        """
        super().__init__(*args, **kwargs)

        self.overwrite = overwrite

    @staticmethod
    def _convert_doc_to_docx(filepath):
        w = wc.Dispatch('Word.Application')
        doc = w.Documents.Open(filepath)
        new_filepath = filepath.with_name(filepath.name + 'x')
        doc.SaveAs(new_filepath, 16)

        return new_filepath

    @staticmethod
    def _convert_docx_to_pdf(filepath):
        new_filepath = filepath.with_name(filepath.name.replace('.docx', '.pdf'))

        # import pythoncom
        # pythoncom.CoInitializeEx(0) # todo remove
        docx2pdf.convert(filepath, new_filepath)

        return new_filepath

    def apply(self, file_path: Union[Path, str]) -> Path:
        file_path = Path(file_path)
        try:
            if file_path.name.lower().endswith('.doc'):
                file_path = ConvertToPdf._convert_doc_to_docx(file_path)

            if file_path.name.lower().endswith('.docx'):
                file_path = ConvertToPdf._convert_docx_to_pdf(file_path)

            if file_path.name.lower().endswith('.pdf'):
                return file_path

        except Exception as e:
            if self.errors == 'ignore':
                return None

            elif self.errors == 'print':
                print(e)
                print(file_path)
                return None

            elif self.errors == 'raise':
                raise e

        raise Exception('Unable to convert file: ' + str(file_path))
