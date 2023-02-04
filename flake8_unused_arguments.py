import ast
import optparse
from ast import NodeVisitor, Store
from typing import Iterable, List, Tuple, Union

import flake8.options.manager


FunctionTypes = Union[ast.AsyncFunctionDef, ast.FunctionDef, ast.Lambda]
LintResult = Tuple[int, int, str, str]


class Plugin:
    name = "flake8-unused-arguments"
    version = "0.0.13"

    ignore_abstract = False
    ignore_overload = False
    ignore_override = False
    ignore_stubs = False
    ignore_variadic_names = False
    ignore_lambdas = False
    ignore_nested_functions = False
    ignore_dunder_methods = False

    def __init__(self, tree: ast.Module):
        self.tree = tree

    @classmethod
    def add_options(cls, option_manager: flake8.options.manager.OptionManager) -> None:
        option_manager.add_option(
            "--unused-arguments-ignore-abstract-functions",
            action="store_true",
            parse_from_config=True,
            default=cls.ignore_abstract,
            dest="unused_arguments_ignore_abstract_functions",
            help="If provided, then unused arguments for functions decorated with abstractmethod will be ignored.",
        )

        option_manager.add_option(
            "--unused-arguments-ignore-overload-functions",
            action="store_true",
            parse_from_config=True,
            default=cls.ignore_overload,
            dest="unused_arguments_ignore_overload_functions",
            help="If provided, then unused arguments for functions decorated with overload will be ignored.",
        )

        option_manager.add_option(
            "--unused-arguments-ignore-override-functions",
            action="store_true",
            parse_from_config=True,
            default=cls.ignore_override,
            dest="unused_arguments_ignore_override_functions",
            help="If provided, then unused arguments for functions decorated with override will be ignored.",
        )

        option_manager.add_option(
            "--unused-arguments-ignore-stub-functions",
            action="store_true",
            parse_from_config=True,
            default=cls.ignore_stubs,
            dest="unused_arguments_ignore_stub_functions",
            help="If provided, then unused arguments for functions that are only a pass statement will be ignored.",
        )

        option_manager.add_option(
            "--unused-arguments-ignore-variadic-names",
            action="store_true",
            parse_from_config=True,
            default=cls.ignore_variadic_names,
            dest="unused_arguments_ignore_variadic_names",
            help="If provided, then unused *args and **kwargs won't produce warnings.",
        )

        option_manager.add_option(
            "--unused-arguments-ignore-lambdas",
            action="store_true",
            parse_from_config=True,
            default=cls.ignore_lambdas,
            dest="unused_arguments_ignore_lambdas",
            help="If provided, all lambdas are ignored.",
        )

        option_manager.add_option(
            "--unused-arguments-ignore-nested-functions",
            action="store_true",
            parse_from_config=True,
            default=cls.ignore_nested_functions,
            dest="unused_arguments_ignore_nested_functions",
            help=(
                "If provided, only functions at the top level of a module or "
                "methods of a class in the top level of a module are checked."
            ),
        )

        option_manager.add_option(
            "--unused-arguments-ignore-dunder",
            action="store_true",
            parse_from_config=True,
            default=cls.ignore_dunder_methods,
            dest="unused_arguments_ignore_dunder_methods",
            help=(
                "If provided, all double-underscore methods are ignored, e.g., __new__, _init__, "
                "__enter__, __exit__, __reduce_ex__, etc."
            ),
        )

    @classmethod
    def parse_options(cls, options: optparse.Values) -> None:
        cls.ignore_abstract = options.unused_arguments_ignore_abstract_functions
        cls.ignore_overload = options.unused_arguments_ignore_overload_functions
        cls.ignore_override = options.unused_arguments_ignore_override_functions
        cls.ignore_stubs = options.unused_arguments_ignore_stub_functions
        cls.ignore_variadic_names = options.unused_arguments_ignore_variadic_names
        cls.ignore_lambdas = options.unused_arguments_ignore_lambdas
        cls.ignore_nested_functions = options.unused_arguments_ignore_nested_functions
        cls.ignore_dunder_methods = options.unused_arguments_ignore_dunder_methods

    def run(self) -> Iterable[LintResult]:
        finder = FunctionFinder(self.ignore_nested_functions)
        finder.visit(self.tree)

        for function in finder.functions:
            decorator_names = set(get_decorator_names(function))

            # ignore overload functions, it's not a surprise when they're empty
            if self.ignore_overload and "overload" in decorator_names:
                continue

            # ignore overridden functions
            if self.ignore_override and "override" in decorator_names:
                continue

            # ignore abstractmethods, it's not a surprise when they're empty
            if self.ignore_abstract and "abstractmethod" in decorator_names:
                continue

            # ignore stub functions
            if self.ignore_stubs and is_stub_function(function):
                continue

            # ignore lambdas
            if self.ignore_lambdas and isinstance(function, ast.Lambda):
                continue

            # ignore __double_underscore_methods__()
            if self.ignore_dunder_methods and is_dunder_method(function):
                continue

            for i, argument in get_unused_arguments(function):
                name = argument.arg
                if self.ignore_variadic_names:
                    if function.args.vararg and function.args.vararg.arg == name:
                        continue
                    if function.args.kwarg and function.args.kwarg.arg == name:
                        continue

                # ignore self or whatever the first argument is for a classmethod
                if i == 0 and (name == "self" or "classmethod" in decorator_names):
                    continue

                line_number = argument.lineno
                offset = argument.col_offset

                if name.startswith("_"):
                    error_code = "U101"
                else:
                    error_code = "U100"

                text = "{error_code} Unused argument '{name}'".format(
                    error_code=error_code, name=name
                )
                check = "unused argument"
                yield (line_number, offset, text, check)


def get_unused_arguments(function: FunctionTypes) -> List[Tuple[int, ast.arg]]:
    """Generator that yields all of the unused arguments in the given function."""
    arguments = list(enumerate(get_arguments(function)))

    class NameFinder(NodeVisitor):
        def visit_Name(self, name: ast.Name) -> None:
            nonlocal arguments
            if isinstance(name.ctx, Store):
                return

            arguments = [
                (arg_index, arg) for arg_index, arg in arguments if arg.arg != name.id
            ]

    NameFinder().visit(function)

    return arguments


def get_arguments(function: FunctionTypes) -> List[ast.arg]:
    """Get all of the argument names of the given function."""
    args = function.args

    ordered_arguments: List[ast.arg] = []

    # plain old args
    ordered_arguments.extend(args.args)

    # *arg name
    if args.vararg is not None:
        ordered_arguments.append(args.vararg)

    # *, key, word, only, args
    ordered_arguments.extend(args.kwonlyargs)

    # **kwarg name
    if args.kwarg is not None:
        ordered_arguments.append(args.kwarg)

    return ordered_arguments


def get_decorator_names(function: FunctionTypes) -> Iterable[str]:
    if isinstance(function, ast.Lambda):
        return

    for decorator in function.decorator_list:
        if isinstance(decorator, ast.Name):
            yield decorator.id
        elif isinstance(decorator, ast.Attribute):
            yield decorator.attr
        elif isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Name):
                yield decorator.func.id
            else:
                yield decorator.func.attr  # type: ignore
        else:
            assert False, decorator


def is_stub_function(function: FunctionTypes) -> bool:
    if isinstance(function, ast.Lambda):
        return isinstance(function.body, ast.Ellipsis)

    statement = function.body[0]
    if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Str):
        if len(function.body) > 1:
            # first statement is a docstring, let's skip it
            statement = function.body[1]
        else:
            # it's a function with only a docstring, that's a stub
            return True

    if isinstance(statement, ast.Pass):
        return True
    if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Ellipsis):
        return True

    if isinstance(statement, ast.Raise):
        # raise NotImplementedError()
        if (
            isinstance(statement.exc, ast.Call)
            and hasattr(statement.exc.func, "id")
            and statement.exc.func.id == "NotImplementedError"
        ):
            return True

        # raise NotImplementedError
        elif (
            isinstance(statement.exc, ast.Name)
            and hasattr(statement.exc, "id")
            and statement.exc.id == "NotImplementedError"
        ):
            return True

    return False


def is_dunder_method(function: FunctionTypes) -> bool:
    if isinstance(function, ast.Lambda):
        return False

    if not hasattr(function, "name"):
        return False

    name = function.name
    return len(name) > 4 and name.startswith("__") and name.endswith("__")


class FunctionFinder(NodeVisitor):
    functions: List[FunctionTypes]

    def __init__(self, only_top_level: bool = False) -> None:
        super().__init__()
        self.functions = []
        self.only_top_level = only_top_level

    def visit_function_types(self, function: FunctionTypes) -> None:
        self.functions.append(function)
        if self.only_top_level:
            return
        if isinstance(function, ast.Lambda):
            self.visit(function.body)
        else:
            for obj in function.body:
                self.visit(obj)

    visit_AsyncFunctionDef = visit_FunctionDef = visit_Lambda = visit_function_types  # type: ignore[assignment]
