Start a project
===============

BERNARD has a built-in template that can be used to start a new project.
Onces that you have [installed](./install.md) the `bernard` package, you
can use it like this:

```bash
bernard start_project proj_name ~/dev/proj_name
```

This will automatically create a simplet emplate for a project named
`proj_name` in the directory `~/dev/proj_name`.

Please note the following requirements:

- The project name is expected to be a valid lower-case and snake-case
  Python variable name.
- The target directory must be empty or contain only hidden files.

## Project structure

The created project will have a few files that you can customize. While
we will not explain what `.editorconfig`, `.gitignore`,
`requirements.txt` and `README.md` do, we will dive into
BERNARD-specific files.

### `manage.py`

This is an alias to the `bernard` command with one subtle difference:
the `BERNARD_SETTINGS_FILE` environment variable is set automatically.
That can be useful depending on how you configure your project and if
you use environment variables to do so.

### `env`

That's a sample environment file. You can source it:

```bash
source ./env
```

This will automatically load the default config. You need to update it
with configuration values that suit your needs.

The "Env File" PyCharm plugin can be used to automatically read this
file in each run environment.

### `src/proj_name/settings.py`

Here are the settings of the project. Settings can be accessed from
anywhere in the code by doing this:

```python
from bernard.conf import settings

print(settings.MY_SETTING)
```

The configuration file is evaluated in a sandbox at startup time. You
can put logic in there, but do not ever import it directly from BERNARD
or reciprocically.

All variables with an uppercase name will be imported into `settings`,
however lowercase variables will not be available.

### `src/proj_name/states.py`

In this file you can find your default state as well as all the states
of your bot that you will develop.

### `src/proj_name/transitions.py`

The transitions file has all the triggers of the bot. It's the starting
point of the framework, which will read it to discover both transitions
and states.

## Wrap-up

There is a `bernard start_project` command that allows to quickly create
a project from a simple template. It has all the basic files required
to make a BERNARD project.

**Next step**: [number bot](./number-bot.md)
