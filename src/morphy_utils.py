from collections.abc import Iterable
from functools import reduce, partial
from operator import itemgetter, attrgetter
from typing import Dict, Tuple, List, Union, Callable

import pymorphy2
from more_itertools import locate
from pymorphy2.analyzer import Parse

from src.utils import identity, compose

morph_analyzer = pymorphy2.MorphAnalyzer(lang='ru')


def invert_dict(d):
    d2 = {}
    for k, V in d.items():
        if isinstance(V, Iterable):
            for v in V:
                d2[v] = k
        else:
            d2[V] = k
    return d2


_pos_by_name = {
    'сущ': ('NOUN',),
    'прил': ('ADJF', 'ADJS'),
    'глаг': ('VERB',),
    'инф': ('INFN',),
    'прич': ('PRTF', 'PRTS'),
    'дееприч': ('GRND',),
    'числ': ('NUMR',),
    'нар': ('ADVB',),
    'мест': ('NPRO',),
    'предл': ('PREP',),
    'союз': ('CONJ',),
    'частица': ('PRCL',),
}
_name_by_pos = invert_dict(_pos_by_name)

_case_by_name = {
    'и': ('nomn',),         # именительный Кто? Что?	хомяк ест
    'р': ('gent', 'gen2'),  # родительный  Кого? Чего?	у нас нет хомяка
    'д': ('datv',),         # дательный    Кому? Чему?	сказать хомяку спасибо
    'в': ('accs', 'acc2'),  # винительный  Кого? Что?	хомяк читает книгу
    'т': ('ablt',),         # творительный Кем? Чем?	зерно съедено хомяком
    'п': ('loct', 'loc2'),  # предложный   О ком? О чём?
    'з': ('voct',),         # звательный   Его формы используются при обращении к человеку.	Саш, пойдем в кино.
    'ignore': None,
}
_name_by_case = invert_dict(_case_by_name)


def f(seq, next_tokens):
    if next_tokens:
        for tok in next_tokens[0]:
            for r in f((*seq, tok), next_tokens[1:]):
                yield r
    else:
        yield seq


def encode_masks(*masks, dct=None):
    dct = dct or _pos_by_name
    return reduce(
        tuple.__add__,
        tuple(map(tuple, map(
            partial(f, ()),
            (
                tuple(map(dct.get, mask))
                for mask in masks
            )
        )))
    )


def matches_masks(lst, masks: tuple[tuple], key=identity):
    # print(lst, list(map(key, lst)), mask)
    return tuple(map(key, lst)) in masks


def matches_pos_mask(text: Union[List[Parse], List[str]], pos_mask: Tuple[str, ...]):
    return matches_masks(
        text,
        encode_masks(pos_mask, _pos_by_name),
        key=compose(
            compose(morph_analyzer.parse, itemgetter(0))
            if isinstance(text[0], str)
            else identity,
            attrgetter('tag'),
            attrgetter('POS')
        )
    )


def decline_case(text: Union[List[Parse], List[str]], cases_by_mask: Dict[Tuple[str, ...], Tuple[str, ...]]):
    if not text:
        return []

    if isinstance(text[0], str):
        text = list(map(itemgetter(0), map(morph_analyzer.parse, text)))

    masks = list(cases_by_mask.keys())
    mask_indexes = list(locate(masks, partial(matches_pos_mask, text)))
    res = []

    for mask in map(masks.__getitem__, mask_indexes):
        declined = []
        for word, case_name in zip(text, cases_by_mask[mask]):
            case = _case_by_name[case_name]
            if case is None:
                declined.append(word)

            else:
                declined.append(word.inflect({case[0]}))

        res.append(tuple(declined))

    return res


def eq(obj):
    return obj.__eq__



def Matcher(mask: Iterable[Iterable[Callable]]):
    filters = []
    for i, predicates in enumerate(mask):
        filters.append(compose(itemgetter(i), *predicates))

    return lambda words: len(words) == len(mask) and all(map(lambda f: f(words), filters))


def Apply(mask: Iterable[Iterable[Callable]]):
    mappers = []
    for i, mappers_ in enumerate(mask):
        mappers.append(compose(itemgetter(i), *mappers_))

    return lambda *args, **kwargs: list(map(lambda m: m(*args, **kwargs), mappers))

