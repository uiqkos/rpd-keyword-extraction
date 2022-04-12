from functools import reduce
from itertools import filterfalse
from typing import Iterable

from more_itertools import ilen

from src.stages.cluster.basegrouper import BaseGrouper
from src.stages.cluster.pool import PoolFactory
from src.utils import compose


class Grouper(BaseGrouper):
    def __init__(
        self,
        pool_factory: PoolFactory,
        intersection: bool = True,
        *args, **kwargs
    ):
        """
        Объединяет ключевые слова с использованием Pool

        Parameters
        ----------
        pool_factory: PoolFactory
            фабрика пулов
        intersection: bool
            Пересечение групп
        """
        super(Grouper, self).__init__(*args, collect_inputs=True, **kwargs)

        self.intersection = intersection
        self.pool_factory = pool_factory

    def apply(self, docs: Iterable[Iterable[str]]):
        docs = reduce(set.__or__, map(set, docs))
        docs.remove('')

        pool = self.pool_factory.create(docs)

        groups = pool.reduce(
            continue_if_merge=self.intersection,
            verbose=self.verbose,
            reshape=True
        )

        if self.save:
            pc = round((ilen(filterfalse(compose(len, (1).__eq__), groups)) / len(groups)), 2)
            self._save_groups(groups, {'pc': pc})

        return groups
