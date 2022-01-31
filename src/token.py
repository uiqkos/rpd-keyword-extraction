from dataclasses import dataclass, field
from typing import Callable

from src.utils import identity
from src.features.text_preprocessing import normalize


class Token:
    def __init__(self, text):
        self.text = text
        # self.normal_form = normalize(text)
        # self.normalize = normalize or identity

    @property
    def normal_form(self):
        return normalize(self.text)

    def __str__(self):
        return f'{self.text} ({self.normal_form})'

    def __repr__(self):
        return self.__str__()

    def __hash__(self):
        return hash(self.normal_form)

    def __eq__(self, other):
        return other.normal_form == self.normal_form
