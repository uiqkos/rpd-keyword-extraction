from typing import Callable, Iterable

import numpy as np

from src.utils import tqdm


class Pool:
    def __init__(
        self,
        objects,
        group_comparator: Callable[[Iterable, Iterable], bool]
    ):
        """
        Пул объектов.

        Parameters
        ----------
        objects
        group_comparator: (Iterable, Iterable) -> bool
            Сравнивает группы ключевых слов и возвращает True, если группы можно объединить и False, если нет
        """
        self.group_comparator = group_comparator
        self.objects = objects

    def reduce(self, continue_if_merge=False, verbose=True, reshape=True) -> list[np.array]:
        new_items = []

        objects = verbose and tqdm(self.objects) or self.objects

        for group1 in objects:
            if reshape:
                group1 = [group1]

            merged = False

            for i in range(len(new_items)):
                if self.group_comparator(group1, new_items[i]):
                    new_items[i] += group1
                    merged = True
                    if not continue_if_merge:
                        break

            if not merged or continue_if_merge:
                new_items.append(group1)

        return new_items


class PoolFactory:
    def __init__(self, group_comparator: Callable[[Iterable, Iterable], bool]):
        self.group_comparator = group_comparator

    def create(self, objects):
        return Pool(objects, self.group_comparator)
