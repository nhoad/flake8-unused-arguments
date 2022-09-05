import ast
import re
import subprocess
import textwrap
from contextlib import nullcontext
from unittest.mock import patch

import pytest


@pytest.mark.parametrize(
    "function, expected_names",
    [
        ("def foo(a, b, c): pass", ["a", "b", "c"]),
        ("def foo(a, b, *, c): pass", ["a", "b", "c"]),
        ("def foo(a, b, *, c=5): pass", ["a", "b", "c"]),
        ("def foo(*args): pass", ["args"]),
        ("def foo(**kwargs): pass", ["kwargs"]),
        (
            "def foo(a, b, *args, c, d=5, e, **kwargs): pass",
            ["a", "b", "args", "c", "d", "e", "kwargs"],
        ),
        ("async def foo(a, b, c): pass", ["a", "b", "c"]),
        ("async def foo(a, b, *, c): pass", ["a", "b", "c"]),
        ("async def foo(a, b, *, c=5): pass", ["a", "b", "c"]),
        ("async def foo(*args): pass", ["args"]),
        ("async def foo(**kwargs): pass", ["kwargs"]),
        (
            "async def foo(a, b, *args, c, d=5, e, **kwargs): pass",
            ["a", "b", "args", "c", "d", "e", "kwargs"],
        ),
        (
            """
        class foo:
            def bar(self, cool):
                pass
    """,
            ["self", "cool"],
        ),
        ("l = lambda g: 5", ["g"]),
    ],
)
def test_get_argument_names(function, expected_names):
    from flake8_unused_arguments import get_arguments

    argument_names = [a.arg for a in get_arguments(get_function(function))]
    print(argument_names)
    print(expected_names)
    assert argument_names == expected_names


@pytest.mark.parametrize(
    "function, expected_names",
    [
        ("def foo(a, b, c): return a + b", ["c"]),
        (
            """
        class foo:
            def bar(self, cool):
                self.thing = cool
    """,
            [],
        ),
        (
            """
        def external(a, b, c):
            def internal():
                a + b
    """,
            ["c"],
        ),
        ("l = lambda g: 5", ["g"]),
    ],
)
def test_get_unused_arguments(function, expected_names):
    from flake8_unused_arguments import get_unused_arguments

    argument_names = [a.arg for _, a in get_unused_arguments(get_function(function))]
    print(argument_names)
    print(expected_names)
    assert argument_names == expected_names


@pytest.mark.parametrize(
    "function, expected_result",
    [
        (
            """
    @a
    @thing.b
    @thing.c()
    @d()
    def foo():
        pass
    """,
            ["a", "b", "c", "d"],
        ),
        ("lambda g: 5", []),
    ],
)
def test_get_decorator_names(function, expected_result):
    from flake8_unused_arguments import get_decorator_names

    function_names = list(get_decorator_names(get_function(function)))
    assert function_names == expected_result


@pytest.mark.parametrize(
    "function, expected_result",
    [
        ("def foo():\n 'with docstring'\n pass", True),
        ("def foo():\n 'with docstring'", True),
        ("def foo():\n 'with docstring'\n ...", True),
        ("def foo():\n 'with docstring'\n return 5", False),
        ("def foo():\n 'string' + 'with docstring'\n ...", False),
        ("def foo():\n f = 'string' + 'with docstring'\n ...", False),
        ("def foo(): pass", True),
        ("def foo(): ...", True),
        ("def foo(): return 5", False),
        ("def foo(): raise NotImplementedError()", True),
        ("def foo(): raise NotImplementedError", True),
        ("def foo(): raise NotImplementedError()", True),
        ("def foo(): raise NotImplementedError", True),
        ("def foo(): raise SomethingElse()", False),
        ("def foo(): raise object.error()", False),
        ("def foo(): raise object.error", False),
        ("def foo(): raise value", False),
        ("def foo(): raise 'cool string'", False),
        ("def foo(): raise", False),
        ("lambda: ...", True),
        ("lambda: 5", False),
        (
            """
    def foo():
        a = 5
        return 5
    """,
            False,
        ),
        (
            """
    def foo():
        if 5:
            return
        else:
            return
    """,
            False,
        ),
    ],
)
def test_is_stub_function(function, expected_result):
    from flake8_unused_arguments import is_stub_function

    assert is_stub_function(get_function(function)) == expected_result


@pytest.mark.parametrize(
    "function, options, expected_warnings",
    [
        (
            """
    @abstractmethod
    def foo(a):
        pass
    """,
            {"ignore_abstract": False},
            [(3, 8, "U100 Unused argument 'a'", "unused argument")],
        ),
        (
            """
    @abstractmethod
    def foo(a):
        pass
    """,
            {"ignore_abstract": True},
            [],
        ),
        (
            """
    @overload
    def foo(a):
        pass
    """,
            {"ignore_overload": False},
            [(3, 8, "U100 Unused argument 'a'", "unused argument")],
        ),
        (
            """
    @overload
    def foo(a):
        pass
    """,
            {"ignore_overload": True},
            [],
        ),
        (
            """
    def foo(a):
        pass
    """,
            {"ignore_stubs": False},
            [(2, 8, "U100 Unused argument 'a'", "unused argument")],
        ),
        (
            """
    def foo(a):
        pass
    """,
            {"ignore_stubs": True},
            [],
        ),
        (
            """
    def foo(*args):
        pass
    """,
            {"ignore_variadic_names": True},
            [],
        ),
        (
            """
    def foo(**kwargs):
        pass
    """,
            {"ignore_variadic_names": True},
            [],
        ),
        (
            """
    def foo(*args):
        pass
    """,
            {"ignore_variadic_names": False},
            [(2, 9, "U100 Unused argument 'args'", "unused argument")],
        ),
        (
            """
    def foo(**kwargs):
        pass
    """,
            {"ignore_variadic_names": False},
            [(2, 10, "U100 Unused argument 'kwargs'", "unused argument")],
        ),
        (
            "foo = lambda a: 1\n",
            {"ignore_lambdas": True},
            [],
        ),
        (
            "foo = lambda a: 1\n",
            {"ignore_lambdas": False},
            [(1, 13, "U100 Unused argument 'a'", "unused argument")],
        ),
        (
            """
            def foo(a):
                def bar(b):
                    pass
            zed = lambda c: lambda d: 1
            """,
            {"ignore_nested_functions": False},
            [
                (2, 8, "U100 Unused argument 'a'", "unused argument"),
                (3, 12, "U100 Unused argument 'b'", "unused argument"),
                (5, 13, "U100 Unused argument 'c'", "unused argument"),
                (5, 23, "U100 Unused argument 'd'", "unused argument"),
            ],
        ),
        (
            """
            def foo(a):
                def bar(b):
                    pass
            zed = lambda c: lambda d: 1
            """,
            {"ignore_nested_functions": True},
            [
                (2, 8, "U100 Unused argument 'a'", "unused argument"),
                (5, 13, "U100 Unused argument 'c'", "unused argument"),
            ],
        ),
        (
            """
            class Foo:
                def __new__(cls):
                    return []
                def __enter__(self):
                    return self
                def __exit__(self, exc_tp, exc_v, exc_tb):
                    return False
                def __setattr__(self, item, value):
                    raise ValueError("read-only")
                def __reduce_ex__(self, protocol):
                    return Foo, ()
            """,
            {"ignore_dunder_methods": False},
            [
                (3, 16, "U100 Unused argument 'cls'", "unused argument"),
                (7, 23, "U100 Unused argument 'exc_tp'", "unused argument"),
                (7, 31, "U100 Unused argument 'exc_v'", "unused argument"),
                (7, 38, "U100 Unused argument 'exc_tb'", "unused argument"),
                (9, 26, "U100 Unused argument 'item'", "unused argument"),
                (9, 32, "U100 Unused argument 'value'", "unused argument"),
                (11, 28, "U100 Unused argument 'protocol'", "unused argument"),
            ],
        ),
        (
            """
            class Foo:
                def __new__(cls):
                    return []
                def __enter__(self):
                    return self
                def __exit__(self, exc_tp, exc_v, exc_tb):
                    return False
                def __setattr__(self, item, value):
                    raise ValueError("read-only")
                def __reduce_ex__(self, protocol):
                    return Foo, ()
            """,
            {"ignore_dunder_methods": True},
            [],
        ),
        (
            """
    def foo(_a):
        pass
    """,
            {},
            [(2, 8, "U101 Unused argument '_a'", "unused argument")],
        ),
        (
            """
    def foo(self):
        pass
    """,
            {},
            [],
        ),
        (
            """
    @classmethod
    def foo(cls):
        pass
    """,
            {},
            [],
        ),
        (
            """
    @classmethod
    def foo(cls, bar):
        use(cls)
    """,
            {},
            [(3, 13, "U100 Unused argument 'bar'", "unused argument")],
        ),
        (
            """
    def cool(a):
        def inner(b):
            pass
        async def async_inner(c):
            pass
    async def async_cool(d):
        def inner(e):
            pass
        async def async_inner(f):
            pass
    """,
            {},
            [
                (2, 9, "U100 Unused argument 'a'", "unused argument"),
                (3, 14, "U100 Unused argument 'b'", "unused argument"),
                (5, 26, "U100 Unused argument 'c'", "unused argument"),
                (7, 21, "U100 Unused argument 'd'", "unused argument"),
                (8, 14, "U100 Unused argument 'e'", "unused argument"),
                (10, 26, "U100 Unused argument 'f'", "unused argument"),
            ],
        ),
        (
            """
    # make sure we detect variables as used when they're referenced in an inner function
    def cool(a):
        def inner(c):
            a()
    """,
            {},
            [(4, 14, "U100 Unused argument 'c'", "unused argument")],
        ),
    ],
)
def test_integration(function, options, expected_warnings):
    from flake8_unused_arguments import Plugin

    with patch.multiple(Plugin, **options) if options else nullcontext():
        plugin = Plugin(ast.parse(textwrap.dedent(function)))
        warnings = list(plugin.run())
        print(function)
        print(warnings)
        assert warnings == expected_warnings


@pytest.mark.release
def test_check_version() -> None:
    from flake8_unused_arguments import Plugin

    assert get_most_recent_tag() == Plugin.version


FF_CODE = """
def some_function(a=1):
    def some_nested_function(b=1):
        return b
    return some_nested_function(a)

class SomeClass:
    def some_method(a=1):
        def some_nested_method(b=1):
            return b
        return some_nested_method(a)
"""
FF_ALL_FUNCTIONS = [
    "some_function",
    "some_nested_function",
    "some_method",
    "some_nested_method",
]


@pytest.mark.parametrize(
    "only_top_level, expected",
    [
        (False, FF_ALL_FUNCTIONS),
        (True, [n for n in FF_ALL_FUNCTIONS if "nested" not in n]),
    ],
)
def test_function_finder(only_top_level, expected):
    from flake8_unused_arguments import FunctionFinder

    finder = FunctionFinder(only_top_level=only_top_level)
    finder.visit(ast.parse(FF_CODE))
    names = [node.name for node in finder.functions]

    assert names == expected


@pytest.mark.parametrize(
    "code, expected_value",
    [
        ("def foo(): pass", False),
        ("def __foo(): pass", False),
        ("def foo__(): pass", False),
        ("def __foo__(): pass", True),
        ("async def foo(): pass", False),
        ("async def __foo(): pass", False),
        ("async def foo__(): pass", False),
        ("async def __foo__(): pass", True),
        ("lambda: None", False),
    ]
)
def test_is_dunder_method(code, expected_value):
    from flake8_unused_arguments import is_dunder_method
    func = ast.parse(textwrap.dedent(code)).body[0]

    if isinstance(func, ast.Expr):
        func = func.value

    assert is_dunder_method(func) == expected_value


def get_most_recent_tag() -> str:
    return (
        re.sub("^v", "", subprocess.check_output(["git", "describe", "--tags", "--abbrev=0"], text=True)
        .strip())
    )


def get_function(text):
    from flake8_unused_arguments import FunctionFinder

    finder = FunctionFinder()
    finder.visit(ast.parse(textwrap.dedent(text)))
    return finder.functions[0]
