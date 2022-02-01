import os
import re
import time
import urllib.request as request
from typing import Set

import pandas as pd
from tqdm import tqdm as progressbar

from src.settings import DATA_PATH


def existing_file_ids() -> Set[str]:
    file_names = list(zip(*os.walk(DATA_PATH.joinpath('documents'))))[2][0]
    id_pattern = re.compile(r'^\((\d+)\)')
    return {int(re.findall(id_pattern, file_name)[0]) for file_name in file_names}


def load_docs():
    raw_data_path = DATA_PATH.joinpath('raw', 'data.csv')
    docs_data_path = DATA_PATH.joinpath('documents')

    data = pd.read_csv(raw_data_path, header=0)
    ignore_ids = existing_file_ids()

    for file_name, file_id, url in progressbar(data[['FILE_NAME', 'FILE_ID', 'URL']].values, ncols=100):
        if file_id in ignore_ids:
            continue

        file_name = re.sub(r'[^\w\-_\. ]', '', file_name)
        _, msg = request.urlretrieve(url, docs_data_path.joinpath(f"({file_id}) {file_name}"))
        time.sleep(1)


if __name__ == '__main__':
    load_docs()
