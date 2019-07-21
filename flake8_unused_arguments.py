import ast
from ast import NodeVisitor, Store
from typing import Iterable, List, Tuple, Union


FunctionTypes = Union[ast.AsyncFunctionDef, ast.FunctionDef, ast.Lambda]
LintResult = Tuple[int, int, str, str]

ERROR_CODE = "U100"


class Plugin:
    name = "flake8-unusedarguments"
    version = "1.0.0"

    def __init__(self, tree: ast.Module):
        self.tree = tree

    def run(self) -> Iterable[LintResult]:
        functions: List[FunctionTypes] = []

        class FunctionFinder(NodeVisitor):
            def visit_AsyncFunctionDef(self, function: ast.AsyncFunctionDef) -> None:
                functions.append(function)

            def visit_FunctionDef(self, function: ast.FunctionDef) -> None:
                functions.append(function)

            def visit_Lambda(self, function: ast.Lambda) -> None:
                functions.append(function)

        FunctionFinder().visit(self.tree)

        for function in functions:
            yield from check_function(function)


def check_function(function: FunctionTypes) -> Iterable[LintResult]:
    """Generator that yields all of the unused arguments in the given function."""
    names = get_argument_names(function)

    class NameFinder(NodeVisitor):
        def visit_Name(self, name: ast.Name) -> None:
            if isinstance(name.ctx, Store):
                return

            if name.id in names:
                names.remove(name.id)

    NameFinder().visit(function)

    for name in names:
        line_number = function.lineno
        offset = function.col_offset
        text = f"{ERROR_CODE} Unused argument '{name}'"
        check = "unused argument"
        yield (line_number, offset, text, check)


def get_argument_names(function: FunctionTypes) -> List[str]:
    """Get all of the argument names of the given function."""
    args = function.args

    names: List[str] = []

    # plain old args
    names.extend(arg.arg for arg in args.args)

    # *arg name
    if args.vararg is not None:
        names.append(args.vararg.arg)

    # **kwarg name
    if args.kwarg is not None:
        names.append(args.kwarg.arg)

    # *, key, word, only, args
    names.extend(arg.arg for arg in args.kwonlyargs)

    return names
