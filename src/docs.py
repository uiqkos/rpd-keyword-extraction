from collections import Counter
from operator import attrgetter

from tqdm import tqdm as progressbar

from src.doc import Doc
from src.utils import file_names_in


class Docs:
    def __init__(self, texts=None, directory_path=None, lazy=False):
        self.file_names = file_names_in(directory_path)
        self.directory = directory_path
        self.lazy = lazy

        if lazy and not directory_path:
            raise

        self.docs = []
        self.counter = Counter()
        self.doc_counter = Counter()

        if texts:
            for text in texts:
                doc = Doc(text)
                if not lazy:
                    self.docs.append(doc)

                self.counter.update(doc.counter)
                self.doc_counter += Counter(doc.counter.keys())
        else:
            for i in progressbar(range(len(self.file_names))):
                doc = self[i]
                self.counter.update(doc.counter)
                self.doc_counter += Counter(doc.counter.keys())

    @classmethod
    def from_directory(cls, path) -> 'Docs':
        return cls(directory_path=path, lazy=True)

    def __getitem__(self, item):
        if self.lazy:
            return Doc(open(
                self.directory.joinpath(self.file_names[item]),
                'r',
                errors='ignore',
                encoding='utf-8'
            ).read().split())

        return self.docs[item]

    @property
    def word_count(self) -> int:
        return sum(self.counter.values())

    def total_frequency(self, word) -> float:
        return self.counter[word] / self.word_count

    def doc_frequency(self, word) -> float:
        return self.doc_counter[word] / sum(self.doc_counter.values())
