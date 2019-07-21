import ast
import textwrap

import pytest


@pytest.mark.parametrize("function, expected_names", [
    ("def foo(a, b, c): pass", {"a", "b", "c"}),
    ("def foo(a, b, *, c): pass", {"a", "b", "c"}),
    ("def foo(a, b, *, c=5): pass", {"a", "b", "c"}),
    ("def foo(*args): pass", {"args"}),
    ("def foo(**kwargs): pass", {"kwargs"}),
    ("def foo(a, b, *args, c, d=5, e, **kwargs): pass", {"a", "b", "args", "c", "d", "e", "kwargs"}),
    ("async def foo(a, b, c): pass", {"a", "b", "c"}),
    ("async def foo(a, b, *, c): pass", {"a", "b", "c"}),
    ("async def foo(a, b, *, c=5): pass", {"a", "b", "c"}),
    ("async def foo(*args): pass", {"args"}),
    ("async def foo(**kwargs): pass", {"kwargs"}),
    ("async def foo(a, b, *args, c, d=5, e, **kwargs): pass", {"a", "b", "args", "c", "d", "e", "kwargs"}),
    ("""
        class foo:
            def bar(self, cool):
                pass
    """, {"self", "cool"}),
    ("l = lambda g: 5", {"g"}),
])
def test_get_argument_names(function, expected_names):
    from flake8_unused_arguments import FunctionFinder, get_argument_names

    finder = FunctionFinder()
    finder.visit(ast.parse(textwrap.dedent(function)))
    argument_names = get_argument_names(finder.functions[0])
    print(argument_names)
    print(expected_names)
    assert argument_names == expected_names


@pytest.mark.parametrize("function, expected_names", [
    ("def foo(a, b, c): return a + b", {"c"}),
    ("""
        class foo:
            def bar(self, cool):
                self.thing = cool
    """, set()),
    ("""
        def external(a, b, c):
            def internal():
                a + b
    """, {"c"}),
    ("l = lambda g: 5", {"g"}),
])
def test_get_unused_arguments(function, expected_names):
    from flake8_unused_arguments import FunctionFinder, get_unused_arguments

    finder = FunctionFinder()
    finder.visit(ast.parse(textwrap.dedent(function)))
    argument_names = get_unused_arguments(finder.functions[0])
    print(argument_names)
    print(expected_names)
    assert argument_names == expected_names
