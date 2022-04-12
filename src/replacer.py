from dataclasses import dataclass
from typing import List, Iterable, Set

from src.stages.cluster.keywordgroup import KeywordGroup


@dataclass
class Replacer:
    """Заменяет ключевые слова на центры групп, в которых они состоят"""
    groups: List[KeywordGroup]

    def replace(self, docs: List[List[str]]) -> Iterable[Set[str]]:
        for doc in docs:
            replaced_doc = set(doc)

            for group in self.groups:
                before = len(replaced_doc)
                replaced_doc.difference_update(group.keywords)

                if len(replaced_doc) < before:
                    replaced_doc.add(group.center)

            yield replaced_doc

