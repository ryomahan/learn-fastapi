import typing
from urllib.parse import SplitResult, urlsplit

from starlette.type import Scope


class URL:
    def __init__(self, url: str = "", scope: typing.Optional[Scope] = None, **components: typing.Any) -> None:
        if scope is not None:
            assert not url, "Cannot set both \"url\" and \"scope\"."
            assert not components, "Cannot set both \"scope\" and \"**commponents\"."

            scheme = scope.get("scheme", "http")
            server = scope.get("server", None)
            path = scope.get("root_path", "") + scope["path"]
            query_string = scope.get("query_string", b"")

            host_header = None
            for key, value in scope["headers"]:
                if key == b"host":
                    host_header = value.decode("latin-1")
                    break

            if host_header is not None:
                url = f"{scheme}://{host_header}{path}"
            elif server is None:
                url = path
            else:
                host, port = server
                default_port = {"http": 80, "https": 443, "ws": 80, "wss": 443}.get(scheme)
                if port == default_port:
                    url = f"{scheme}://{host}{path}"
                else:
                    url = f"{scheme}://{host}:{port}{path}"

            if query_string:
                url += "?" + query_string.decode()
        elif components:
            assert not url, "Cannot set both \"url\" and \"**components\"."
            url = URL("").replace(**components).components.geturl()

        self._url = url


    @property
    def components(self) -> SplitResult:
        if not hasattr(self, "_components"):
            self._components = urlsplit(self._url)
        return self._components

    @property
    def username(self) -> typing.Union[None, str]:
        return self.components.username

    @property
    def password(self) -> typing.Union[None, str]:
        return self.components.password

    @property
    def hostname(self) -> typing.Union[None, str]:
        return self.components.hostname

    @property
    def port(self) -> typing.Optional[int]:
        return self.components.port

    def replace(self, **kwargs: typing.Any) -> "URL":
        if "username" in kwargs or "password" in kwargs or "hostname" in kwargs or "port" in kwargs:
            hostname = kwargs.pop("hostname", self.hostname)
            port = kwargs.pop("port", self.port)
            username = kwargs.pop("username", self.username)
            password = kwargs.pop("password", self.password)

            netloc = hostname
            if port is not None:
                netloc += f":{port}"
            if username is not None:
                userpass = username
                if password is not None:
                    userpass += f":{password}"
                netloc = f"{userpass}@{netloc}"

            kwargs["netloc"] = netloc

        components = self.components._replace(**kwargs)
        return self.__class__(components.geturl())


class URLPath(str):

    def __new__(cls, path: str, protocol: str = "", host: str = "") -> "URLPath":
        assert protocol in ("http", "websocket", "")
        return str.__new__(cls, path)

    def __init__(self, path: str, protocol: str = "", host: str = "") -> None:
        self.protocol = protocol
        self.host = host

    def make_absolute_url(self, base_url: typing.Union[str, URL]) -> str:
        if isinstance(base_url, str):
            pass


class Headers(typing.Mapping[str, str]):

    def __init__(
            self,
            headers: typing.Optional[typing.Mapping[str, str]] = None,
            raw: typing.Optional[typing.List[typing.Tuple[bytes, bytes]]] = None,
            # TODO question | why doesn't use starlette.type.Scope
            scope: typing.Optional[typing.Mapping[str, typing.Any]] = None,
    ):
        self._list: typing.List[typing.Tuple[bytes, bytes]] = []
        if headers is not None:
            assert raw is None, "Cannot set both \"headers\" and \"raw\"."
            assert scope is None, "Cannot set both \"headers\" and \"scope\"."
            self._list = [
                (key.lower().encode("latin-1"), value.encode("latin-1"))
                for key, value in headers.items()
            ]
        elif raw is not None:
            assert scope is None, "Cannot set both \"raw\" and \"scope\""
            self._list = raw
        elif scope is not None:
            self.list = scope["headers"]

    def __getitem__(self, key: str) -> str:
        get_header_key = key.lower().encode("latin-1")
        for header_key, header_value in self._list:
            if header_key == get_header_key:
                return header_value.decode("latin-1")
        raise KeyError(key)

    def __iter__(self) -> typing.Iterator[typing.Any]:
        return iter(self.keys())

    def __len__(self) -> int:
        return len(self._list)


class MutableHeaders(Headers):

    def __setitem__(self, key: str, value: str) -> None:
        set_key = key.lower().encode("latin-1")
        set_value = value.encode("latin-1")

        found_indexes = []
        # 过滤重复项，并记录 index
        for idx, (item_key, item_value) in enumerate(self._list):
            if item_key == set_key:
                found_indexes.append(idx)

        # 删除重复项
        for idx in reversed(found_indexes[1:]):
            del self._list[idx]

        if found_indexes:
            idx = found_indexes[0]
            self._list[idx] = (set_key, set_value)
        else:
            self._list.append((set_key, set_value))


class State:
    """ 一个可以存放任意状态的对象，主要用于 request 和 app """
    _state: typing.Dict[str, typing.Any]

    def __init__(self, state: typing.Optional[typing.Dict[str, typing.Any]] = None) -> None:
        if state is None:
            state = {}
        super().__setattr__("_state", state)

    def __setattr__(self, key: typing.Any, value: typing.Any) -> None:
        self._state[key] = value

    def __getattr__(self, key: typing.Any) -> typing.Any:
        try:
            return self._state[key]
        except KeyError:
            message = "'{}' object has no attribute '{}'"
            raise AttributeError(message.format(self.__class__.__name__, key))

    def __delattr__(self, key: typing.Any) -> None:
        del self._state[key]
