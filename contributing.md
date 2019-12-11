# Contributing to Flowpipe

:+1::tada: Thank you very much for taking the time to contribute! :tada::+1:

## Questions

Please don't hesitate to submit any questions as tickets on github!
Please also note that we have set of [examples](examples) and a [readme](README.md) so you might be able to find answers in there as well.

## Feature Requests, Bug Reports, Ideas

Same as for questions, please submit your feature requests, ideas and bug reports as tickets on github. Any such contribution is very much appreciated as it helps to improve this project further.

## Pull Requests

Please fork the repo, create a branch for your changes and submit a pull request.
Pull requests should follow the below conventions.
Also note that we are always squashing when merging the PRs so don't worry about the number of commits on your PR.

## Compatibility

We want to keep this library backwards compatible to python 2.7 for now. The reason is that I know of two users who still run this package in a python 2.7 environment and I would like to provide support for them (until they have switched to py3).
With that being said, we also aim for compatibility with python 3.6+.

## Unittests

We have an extensive, reliable test suite and we want to keep it that way, so please write sufficient tests for your contributions.
We also want to keep the coverage at 100%. If there are good reasons for not covering parts of the code, please explicitely exclude them either via `# pragma: no cover` directly in the code or by specifying it in the [.coveragerc](.coveragerc) file.
The tests have to pass on travis (py2.7 and py3.6).

## Coding styleguide

We generally follow [pep8](https://www.python.org/dev/peps/pep-0008/) with these additional requirements:

- Single quotes for strings in the code, double quotes for docstrings
- For docstrings please use the [google style](https://github.com/google/styleguide/blob/gh-pages/pyguide.md#38-comments-and-docstrings)

## Release to PyPi

Currently there is no specific release policy enacted, so please state in your Pull Request whether you'd need a new PyPi release after the merge and we will release it.

Generally we release to PyPi by drafting a new release in github, updating the `__version__` in [flowpipe/__init__.py](flowpipe/__init__.py) and then triggering (or waiting for) the travis build.

# Next Steps: Become a Collaborator on github

If you have made some contributions already and want to become more involved in the project please don't hesitate to ask about becoming a collaborator.
