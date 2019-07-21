import ast
from ast import NodeVisitor, Store
from typing import Iterable, List, Set, Tuple, Union


FunctionTypes = Union[ast.AsyncFunctionDef, ast.FunctionDef, ast.Lambda]
LintResult = Tuple[int, int, str, str]


class Plugin:
    name = "flake8-unusedarguments"
    version = "1.0.0"

    ignore_abstract = False
    ignore_stubs = False
    ignore_variadic_names = False

    def __init__(self, tree: ast.Module):
        self.tree = tree

    def run(self) -> Iterable[LintResult]:
        finder = FunctionFinder()
        finder.visit(self.tree)

        for function in finder.functions:
            # ignore abtractmethods, it's not a surprise when they're empty
            if self.ignore_abstract and any(name == "abstractmethod" for name in get_decorator_names(function)):
                continue

            # ignore stub functions
            if self.ignore_stubs and len(function.body) == 1:
                statement = function.body[0]
                if isinstance(statement, ast.Pass):
                    continue
                if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Ellipsis):
                    continue
                # FIXME: ignore if the function is raise NotImplementedError()

            for name in get_unused_arguments(function):
                if self.ignore_variadic_names:
                    if function.args.vararg and function.args.vararg.arg == name:
                        continue
                    if function.args.kwarg.arg and function.args.kwarg.arg == name:
                        continue

                line_number = function.lineno
                offset = function.col_offset

                if name.startswith('_'):
                    error_code = "U101"
                else:
                    error_code = "U100"

                text = "{error_code} Unused argument '{name}'".format(error_code=error_code, name=name)
                check = "unused argument"
                yield (line_number, offset, text, check)


def get_unused_arguments(function: FunctionTypes) -> Set[str]:
    """Generator that yields all of the unused arguments in the given function."""
    names = get_argument_names(function)

    class NameFinder(NodeVisitor):
        def visit_Name(self, name: ast.Name) -> None:
            if isinstance(name.ctx, Store):
                return

            if name.id in names:
                names.remove(name.id)

    NameFinder().visit(function)

    return names


def get_argument_names(function: FunctionTypes) -> Set[str]:
    """Get all of the argument names of the given function."""
    args = function.args

    names: Set[str] = set()

    # plain old args
    names.update(arg.arg for arg in args.args)

    # *arg name
    if args.vararg is not None:
        names.add(args.vararg.arg)

    # **kwarg name
    if args.kwarg is not None:
        names.add(args.kwarg.arg)

    # *, key, word, only, args
    names.update(arg.arg for arg in args.kwonlyargs)

    return names


def get_decorator_names(function: FunctionTypes) -> Iterable[str]:
    for decorator in function.decorator_list:
        if isinstance(decorator, ast.Name):
            yield decorator.id
        elif isinstance(decorator, ast.Attribute):
            yield decorator.attr
        elif isinstance(decorator, ast.Call):
            yield decorator.func.attr
        else:
            assert False, decorator


class FunctionFinder(NodeVisitor):
    functions: List[FunctionTypes]

    def __init__(self) -> None:
        super().__init__()
        self.functions = []

    def visit_AsyncFunctionDef(self, function: ast.AsyncFunctionDef) -> None:
        self.functions.append(function)

    def visit_FunctionDef(self, function: ast.FunctionDef) -> None:
        self.functions.append(function)

    def visit_Lambda(self, function: ast.Lambda) -> None:
        self.functions.append(function)
