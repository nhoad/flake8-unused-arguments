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
