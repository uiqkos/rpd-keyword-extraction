import re
from collections.abc import Iterable
from copy import deepcopy
from functools import reduce, partial
from operator import itemgetter, attrgetter, methodcaller
from typing import Dict, Tuple, List, Union, Callable, Collection

import pymorphy2
from more_itertools import locate
from pymorphy2.analyzer import Parse, MorphAnalyzer
from frozendict import frozendict

from src.utils import identity, compose, and_predicates

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


_poses_by_name = {
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
_name_by_pos = invert_dict(_poses_by_name)
_pos_by_name = {name: poses[0] for name, poses in _poses_by_name.items()}

_cases_by_name = {
    'и': ('nomn',),  # именительный Кто? Что?	хомяк ест
    'р': ('gent', 'gen2'),  # родительный  Кого? Чего?	у нас нет хомяка
    'д': ('datv',),  # дательный    Кому? Чему?	сказать хомяку спасибо
    'в': ('accs', 'acc2'),  # винительный  Кого? Что?	хомяк читает книгу
    'т': ('ablt',),  # творительный Кем? Чем?	зерно съедено хомяком
    'п': ('loct', 'loc2'),  # предложный   О ком? О чём?
    'з': ('voct',),
    'именительный': ('nomn',),
    'родительный': ('gent', 'gen2'),
    'дательный': ('datv',),
    'винительный': ('accs', 'acc2'),
    'творительный': ('ablt',),
    'предложный': ('loct', 'loc2'),
    'звательный': ('voct',),
    'им': ('nomn',),
    'род': ('gent', 'gen2'),
    'дат': ('datv',),
    'вин': ('accs', 'acc2'),
    'твор': ('ablt',),
    'пред': ('loct', 'loc2'),
    'зв': ('voct',),
    'ignore': None,
}
_name_by_case = invert_dict(_cases_by_name)
_case_by_name = {name: cases[0] for name, cases in _cases_by_name.items() if cases}


_number_by_name = {
    'мн': 'plur',
    'ед': 'sing',
}


_gender_by_name = {
    'м': 'masc',
    'ж': 'femn',
    'ср': 'neut',
}


def f(seq, next_tokens):
    if next_tokens:
        for tok in next_tokens[0]:
            for r in f((*seq, tok), next_tokens[1:]):
                yield r
    else:
        yield seq


def encode_masks(*masks, dct=None):
    dct = dct or _poses_by_name
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
        encode_masks(pos_mask, _poses_by_name),
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
            case = _cases_by_name[case_name]
            if case is None:
                declined.append(word)

            else:
                declined.append(word.inflect({case[0]}))

        res.append(tuple(declined))

    return res


def eq(obj):
    return obj.__eq__


class Mask:
    def __init__(self, masks: Dict[Iterable[Callable], Iterable[Callable]], build_func: Callable):
        self.mapper_by_matcher = {}

        for predicates, mappers in masks.items():
            self.mapper_by_matcher[and_predicates(*predicates)] = \
                lambda *args, **kwargs: reduce(
                    build_func, map(lambda mapper: mapper(*args, **kwargs), mappers))

    def match(self, inputs):
        i = 0
        for matcher, mapper in self.mapper_by_matcher.items():
            print(i, matcher(inputs))
            if matcher(inputs):
                return mapper
            i += 1

    def apply(self, inputs):
        if mapper := self.match(inputs):
            return mapper(inputs)
        return inputs


def _parse_or_get(p):
    return morph_analyzer.parse(p)[0] if isinstance(p, str) else p


def apply_or_get(apply):
    # def f_(obj):
    #     print(obj)
    #     res = apply(obj)
    #     print(res)
    #     if res is None:
    #         return obj
    #     return res
    # #
    return lambda obj: res if (res := apply(obj)) is not None else obj


def get_func_or_ide(dct: dict, item):
    return dct[item] if item in dct else item


def debugger(obj):
    print(obj)
    return obj


def MorphMask(masks: Dict[Iterable[Dict[str, str]], Iterable[Dict[str, str]]], **translators):
    # {
    #     (dict(case='сущ', number='plur'), dict(case='сущ'), dict(case='прил')): (
    #     dict(number='plur'), dict(number='plur', case='и'))
    # }
    # translate = partial(get_or_ignore, translators)

    mask_dict = {}
    debug = {}
    j = 0
    for matcher_dicts, mapper_dicts in masks.items():
        matcher = tuple(
            and_predicates(*(
                compose(
                    itemgetter(i),
                    _parse_or_get,
                    attrgetter('tag'),
                    attrgetter(key),
                    eq(translators.setdefault(key, {}).setdefault(value, value))
                ) for key, value in matcher_dict.items()
            )) for i, matcher_dict in enumerate(matcher_dicts)
        )
        print(j)
        j += 1
        mapper = tuple(
            compose(
                itemgetter(i),
                _parse_or_get,
                apply_or_get(lambda o: o.inflect(frozenset(
                    map(
                        lambda key, value: translators.setdefault(key, {}).setdefault(value, value),
                        deepcopy(mapper_dict).keys(), deepcopy(mapper_dict).values()
                    )
                ))),
                attrgetter('word')
            ) for i, mapper_dict in enumerate(deepcopy(mapper_dicts))
        )

        mask_dict[matcher] = mapper

    return Mask(mask_dict, '{} {}'.format)


def decode_mask(mask: str):
    mask = re.findall(r'\w+', mask)
    dict_mask = {}

    for dct, key in (
        (_gender_by_name, 'gender'),
        (_case_by_name, 'case'),
        (_pos_by_name, 'POS'),
        (_number_by_name, 'number')
    ):
        for name in dct:
            if name in mask:
                dict_mask[key] = name
                break

    return frozendict(dict_mask)


if __name__ == '__main__':
    _ = decode_mask
    mm = MorphMask({
        (_('прил'), _('сущ м')): (_('прил м'), _('сущ м')),
        (_('прил'), _('сущ ж')): (_('прил ж'), _('сущ ж'))
    }, case=_case_by_name, POS=_pos_by_name, gender=_gender_by_name, number=_number_by_name)

    data = [
        'нейронный сеть',
        'гибкий мозг'
    ]

    for d in data:
        print(d, '->', mm.apply(d.split()))
