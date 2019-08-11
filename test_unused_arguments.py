import ast
import textwrap
from contextlib import nullcontext
from unittest.mock import patch

import pytest


@pytest.mark.parametrize("function, expected_names", [
    ("def foo(a, b, c): pass", ["a", "b", "c"]),
    ("def foo(a, b, *, c): pass", ["a", "b", "c"]),
    ("def foo(a, b, *, c=5): pass", ["a", "b", "c"]),
    ("def foo(*args): pass", ["args"]),
    ("def foo(**kwargs): pass", ["kwargs"]),
    ("def foo(a, b, *args, c, d=5, e, **kwargs): pass", ["a", "b", "args", "c", "d", "e", "kwargs"]),
    ("async def foo(a, b, c): pass", ["a", "b", "c"]),
    ("async def foo(a, b, *, c): pass", ["a", "b", "c"]),
    ("async def foo(a, b, *, c=5): pass", ["a", "b", "c"]),
    ("async def foo(*args): pass", ["args"]),
    ("async def foo(**kwargs): pass", ["kwargs"]),
    ("async def foo(a, b, *args, c, d=5, e, **kwargs): pass", ["a", "b", "args", "c", "d", "e", "kwargs"]),
    ("""
        class foo:
            def bar(self, cool):
                pass
    """, ["self", "cool"]),
    ("l = lambda g: 5", ["g"]),
])
def test_get_argument_names(function, expected_names):
    from flake8_unused_arguments import get_argument_names

    argument_names = get_argument_names(get_function(function))
    print(argument_names)
    print(expected_names)
    assert argument_names == expected_names


@pytest.mark.parametrize("function, expected_names", [
    ("def foo(a, b, c): return a + b", ["c"]),
    ("""
        class foo:
            def bar(self, cool):
                self.thing = cool
    """, []),
    ("""
        def external(a, b, c):
            def internal():
                a + b
    """, ["c"]),
    ("l = lambda g: 5", ["g"]),
])
def test_get_unused_arguments(function, expected_names):
    from flake8_unused_arguments import get_unused_arguments

    argument_names = get_unused_arguments(get_function(function))
    print(argument_names)
    print(expected_names)
    assert argument_names == expected_names


@pytest.mark.parametrize("function, expected_result", [
    ("""
    @a
    @thing.b
    @thing.c()
    @d()
    def foo():
        pass
    """, ["a", "b", "c", "d"]),
    ("lambda g: 5", []),
])
def test_get_decorator_names(function, expected_result):
    from flake8_unused_arguments import get_decorator_names

    function_names = list(get_decorator_names(get_function(function)))
    assert function_names == expected_result


@pytest.mark.parametrize("function, expected_result", [
    ("def foo(): pass", True),
    ("def foo(): ...", True),
    ("def foo(): return 5", False),
    ("lambda: ...", True),
    ("lambda: 5", False),
    ("""
    def foo():
        a = 5
        return 5
    """, False),
    ("""
    def foo():
        if 5:
            return
        else:
            return
    """, False),
])
def test_is_stub_function(function, expected_result):
    from flake8_unused_arguments import is_stub_function
    assert is_stub_function(get_function(function)) == expected_result


@pytest.mark.parametrize("function, options, expected_warnings", [
    ("""
    @abstractmethod
    def foo(a):
        pass
    """, {"ignore_abstract": False}, [(2, 0, "U100 Unused argument 'a'", 'unused argument')]),
    ("""
    @abstractmethod
    def foo(a):
        pass
    """, {"ignore_abstract": True}, []),
    ("""
    def foo(a):
        pass
    """, {"ignore_stubs": False}, [(2, 0, "U100 Unused argument 'a'", 'unused argument')]),
    ("""
    def foo(a):
        pass
    """, {"ignore_stubs": True}, []),
    ("""
    def foo(*args):
        pass
    """, {"ignore_variadic_names": True}, []),
    ("""
    def foo(**kwargs):
        pass
    """, {"ignore_variadic_names": True}, []),
    ("""
    def foo(*args):
        pass
    """, {"ignore_variadic_names": False}, [(2, 0, "U100 Unused argument 'args'", 'unused argument')]),
    ("""
    def foo(**kwargs):
        pass
    """, {"ignore_variadic_names": False}, [(2, 0, "U100 Unused argument 'kwargs'", 'unused argument')]),
    ("""
    def foo(_a):
        pass
    """, {}, [(2, 0, "U101 Unused argument '_a'", 'unused argument')]),
    ("""
    def foo(self):
        pass
    """, {}, []),
    ("""
    @classmethod
    def foo(cls):
        pass
    """, {}, []),
])
def test_integration(function, options, expected_warnings):
    from flake8_unused_arguments import Plugin

    with patch.multiple(Plugin, **options) if options else nullcontext():
        plugin = Plugin(ast.parse(textwrap.dedent(function)))
        warnings = list(plugin.run())
        print(warnings)
        assert warnings == expected_warnings


def get_function(text):
    from flake8_unused_arguments import FunctionFinder
    finder = FunctionFinder()
    finder.visit(ast.parse(textwrap.dedent(text)))
    return finder.functions[0]
