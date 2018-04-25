# coding: utf-8
import re
from os import (
    chmod,
    makedirs,
    path,
    scandir,
    walk,
)
from random import (
    SystemRandom,
)
from sys import (
    stderr,
)
from typing import (
    Text,
)


def fail(msg):
    """
    In case of failure, display a message and exit(1)
    """

    print(msg, file=stderr)
    exit(1)


def vary_name(name: Text):
    """
    Validates the name and creates variations
    """

    snake = re.match(r'^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$', name)

    if not snake:
        fail('The project name is not a valid snake-case Python variable name')

    camel = [x[0].upper() + x[1:] for x in name.split('_')]

    return {
        'project_name_snake': name,
        'project_name_camel': ''.join(camel),
        'project_name_readable': ' '.join(camel),
    }


def make_random_key() -> Text:
    """
    Generates a secure random string
    """

    r = SystemRandom()
    allowed = \
        'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_+/[]'

    return ''.join([r.choice(allowed) for _ in range(0, 50)])


def make_dir_path(project_dir, root, project_name):
    """
    Generates the target path for a directory
    """

    root = root.replace('__project_name_snake__', project_name)
    real_dir = path.realpath(project_dir)
    return path.join(real_dir, root)


def make_file_path(project_dir, project_name, root, name):
    """
    Generates the target path for a file
    """

    return path.join(make_dir_path(project_dir, root, project_name), name)


def generate_vars(project_name, project_dir):
    """
    Generates the variables to replace in files
    """

    out = vary_name(project_name)
    out['random_key'] = make_random_key()
    out['settings_file'] = make_file_path(
        project_dir,
        project_name,
        path.join('src', project_name),
        'settings.py',
    )

    return out


def get_files():
    """
    Read all the template's files
    """

    files_root = path.join(path.dirname(__file__), 'files')

    for root, dirs, files in walk(files_root):
        rel_root = path.relpath(root, files_root)

        for file_name in files:
            try:
                f = open(path.join(root, file_name), 'r', encoding='utf-8')
                with f:
                    yield rel_root, file_name, f.read(), True
            except UnicodeError:
                f = open(path.join(root, file_name), 'rb')
                with f:
                    yield rel_root, file_name, f.read(), False


def check_target(target_path):
    """
    Checks that the target path is not empty
    """

    if not path.exists(target_path):
        return

    with scandir(target_path) as d:
        for entry in d:
            if not entry.name.startswith('.'):
                fail(f'Target directory "{target_path}" is not empty')


def replace_content(content, project_vars):
    """
    Replaces variables inside the content.
    """

    for k, v in project_vars.items():
        content = content.replace(f'__{k}__', v)

    return content


def copy_files(project_vars, project_dir, files):
    """
    Copies files from the template into their target location. Unicode files
    get their variables replaced here and files with a shebang are set to be
    executable.
    """

    for root, name, content, is_unicode in files:
        project_name = project_vars['project_name_snake']

        if is_unicode:
            content = replace_content(content, project_vars)

        file_path = make_file_path(project_dir, project_name, root, name)
        makedirs(make_dir_path(project_dir, root, project_name), exist_ok=True)

        if is_unicode:
            with open(file_path, 'w') as f:
                f.write(content)

            if content.startswith('#!'):
                chmod(file_path, 0o755)
        else:
            with open(file_path, 'wb') as f:
                f.write(content)


def main(args):
    project_vars = generate_vars(args.project_name, args.dir)
    check_target(args.dir)
    copy_files(project_vars, args.dir, get_files())
