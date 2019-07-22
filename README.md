# flake8-import-order

A flake8 plugin that checks for unused function arguments.

This package adds the following warnings:

 - `U100` - An unused argument.
 - `U101` - An unused argument starting with an underscore

Configuration options also exist:
 - `unused-arguments-ignore-abstract-functions` - don't show warnings for abstract functions.
 - `unused-arguments-ignore-stub-functions` - don't show warnings for empty functions.
 - `unused-arguments-ignore-variadic-names` - don't show warnings for unused *args and **kwargs.
