import typing

T = typing.TypeVar("T")


# TODO question | what's mean
class Convertor(typing.Generic[T]):
    regex: typing.ClassVar[str] = ""

    def convert(self, value: str) -> T:
        # pragma: no cover
        raise NotImplementedError()

    def to_string(self, value: T) -> str:
        # pragma: no cover
        raise NotImplementedError()
