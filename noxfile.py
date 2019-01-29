import nox
import os


@nox.session(python="3.6")
def static_type(session):
    session.install('mypy')
    session.install('-r', 'requirements.txt')

    session.run('mypy', '--ignore-missing-imports', 'flowpipe')


@nox.session(python="3.6")
def pytests(session):
    session.install('-r', 'requirements.txt')
    session.install('-r', 'test-requirements.txt')

    session.run(
        'python',
        '-m'
        'pytest',
        '--spec',
        '-s',
        os.path.join('tests')
    )


