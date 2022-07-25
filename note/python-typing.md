## Sequence
Sequence：序列，一种 iterable
内置的序列类型有 list、str、tuple 和 bytes

## Mapping
collections.abc.Mapping 的泛型版本。用法如下：

## MutableMapping 
collections.abc.MutableMapping 的泛型版本。
可变的映射的抽象基类。

映射：一种支持任意键查找并实现了 Mapping 或 MutableMapping 抽象基类 中所规定方法的容器对象。
此类对象的例子包括 dict, collections.defaultdict, collections.OrderedDict 以及 collections.Counter。

## Callable
Callable[[Arg1Type, Arg2Type], ReturnType] 可执行对象

## Awaitable
Awaitable 为可等待对象 awaitable 提供的类，可以被用于 await 表达式中

## AsyncContextManager 异步上下文管理器
contextlib.AbstractAsyncContextManager 的泛型版本。

一个为实现了 object.__aenter__() 与 object.__aexit__() 的类提供的 abstract base class。 
为 object.__aenter__() 提供的一个默认实现是返回 self 而 object.__aexit__() 是一个默认返回 None 的抽象方法。 

参见 异步上下文管理器 的定义：

异步上下文管理器 是 上下文管理器 的一种，它能够在其 __aenter__ 和 __aexit__ 方法中暂停执行。

异步上下文管理器可在 async with 语句中使用。

object.__aenter__(self)
在语义上类似于 __enter__()，仅有的区别是它必须返回一个 可等待对象。

object.__aexit__(self, exc_type, exc_value, traceback)
在语义上类似于 __exit__()，仅有的区别是它必须返回一个 可等待对象。

## ParamSpec

## TypeVar

泛型

T = TypeVar('T')  # Can be anything
S = TypeVar('S', bound=str)  # Can be any subtype of str
A = TypeVar('A', str, bytes)  # Must be exactly str or bytes
U = TypeVar('U', bound=str|bytes)  # Can be any subtype of the union str|bytes
V = TypeVar('V', bound=SupportsAbs)  # Can be anything with an __abs__ method

## ClassVar

## Pattern
这些类型对应的是从 re.compile() 和 re.match() 返回的类型。 
这些类型（及相应的函数）是 AnyStr 中的泛型并可通过编写 Pattern[str], Pattern[bytes], Match[str] 或 Match[bytes] 来具体指定。