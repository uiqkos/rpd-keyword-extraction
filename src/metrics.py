from src.doc import Doc
from src.docs import Docs


def metric1(docs: Docs, doc: Doc, word: str) -> float:
    return doc.frequency(word) / docs.doc_frequency(word)


def metric2(docs: Docs, doc: Doc, word: str) -> float:
    return doc.frequency(word) * (1 - docs.doc_frequency(word))


def metric3(docs: Docs, doc: Doc, word: str) -> float:
    return 1 - docs.doc_frequency(word)


def metric4(docs: Docs, doc: Doc, word: str) -> float:
    return doc.frequency(word) * (1 - docs.doc_frequency(word))
