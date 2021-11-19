# flake8-unused-arguments

A flake8 plugin that checks for unused function arguments.

This package adds the following warnings:

 - `U100` - An unused argument.
 - `U101` - An unused argument starting with an underscore

Configuration options also exist:
 - `unused-arguments-ignore-abstract-functions` - don't show warnings for abstract functions.
 - `unused-arguments-ignore-stub-functions` - don't show warnings for empty functions.
 - `unused-arguments-ignore-variadic-names` - don't show warnings for unused *args and **kwargs.


## Changelog

0.0.9
 - Check nested functions.
 - Don't crash if an attribute is used in a raise statement.

0.0.8
 - Whoops, report the right version when using flake8 --help.

0.0.7
 - The first unused argument in a @classmethod decorated function wasn't properly detected. Thanks to Sebastian Dietrich for contributing the fix!

0.0.6
 - Stub functions that have docstrings are now correctly detected as stub functions
 - Functions with only a docstring are considered stub functions

0.0.5
 - The positions reported are now for the arguments themselves, rather than the function

0.0.4
 - Wrong project name in the readme, whoopsies

0.0.3
 - treat functions that start with "raise NotImplementedError()" as stub functions

0.0.2
 - fixed error in packaging

0.0.1
 - initial release
