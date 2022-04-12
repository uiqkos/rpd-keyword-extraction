import os
from pathlib import Path

import gensim
from torchnlp.download import download_file_maybe_extract

from src.utils import file_paths


class EmbeddingSource:
    def __init__(self, name, url, filename):
        self.url = url
        self.name = name
        self.filename = filename

    def load(self, directory: Path) -> gensim.models.KeyedVectors:
        emb_directory = directory.joinpath(self.name)
        emb_directory.mkdir(exist_ok=True, parents=True)

        paths = list(filter(lambda p: '.bin' in p.name, file_paths(emb_directory)))

        if paths and (path := paths[0]).exists():
            model = gensim.models.KeyedVectors.load_word2vec_format(
                str(path),
                binary=True
            )
            return model

        download_file_maybe_extract(
            url=self.url,
            directory=str(emb_directory),
            filename=self.filename,
        )

        os.remove(emb_directory / self.filename)

        return self.load(directory)


RuWikiRuscorporaCBOW_300_10_2021 = EmbeddingSource(
    name='ruwikiruscorpora_upos_cbow_300_10_2021',
    filename='ruwikiruscorpora_upos_cbow_300_10_2021.zip',
    url='http://vectors.nlpl.eu/repository/20/220.zip'
)

WebCBOW_300_20_2017 = EmbeddingSource(
    name='web_upos_cbow_300_20_2017',
    filename='web_upos_cbow_300_20_2017.bin.gz',
    url='https://rusvectores.org/static/models/web_upos_cbow_300_20_2017.bin.gz'
)
