Generic layers
==============

Generic layers are layers found in most platforms (not necessarily
guaranteed to be found everywhere though).

## Text-based

The most important layer(s) are the ones revolving around texts. A few
variants exist.

### `Text`

A text layer either yields a regular string either a translated string.
Both usages are valid:

```python
from bernard import layers as lyr
from bernard.i18n import translate as t

# Regular string
text_layer = lyr.Text('foo bar')

# Translated string
text_layer = lyr.Text(t.FOO_BAR)
```

The bottom line is that you should not try to do `text_layer.text` from
a trigger, since it would not necessarily resolve to a usable string.

### `RawText`

The `RawText` layer is the same thing as the `Text` layer except it can
only contain an actual string. All messages received from outside will
be available both as `Text` and `RawText` layers, so if you work on a
trigger that requires to read the text you should prefer using the
`RawText`.

```python
from bernard import layers as lyr
from bernard.i18n import translate as t

# Regular string
text_layer = lyr.RawText('foo bar')
```

### `MultiText`

The translation system allows to split text into separate bubbles. This
is useful to be able to do `self.send(t.WELCOME)` and let the copywriter
write as many bubbles as they want without having to touch the code.

Using the `MultiText` layer instead of the `Text` layer indicates to
the platforms that support it that they should split the text into
several bubbles.

Suppose that your CSV file has this:

```csv
WELCOME+1,Welcome!
WELCOME+2,It's nice to see you here :)
```

Then

```python
class FakeState(FakeAppState):
    async def handle(self):
        self.send(lyr.Text(t.WELCOME))
        # Bot: Welcome! It's nice to see you here :)

        self.send(lyr.MultiText(t.WELCOME))
        # Bot: Welcome!
        # Bot: It's nice to see you here :)
```

### `Markdown`

It's like `Text` except that the resulting string will be rendered as
Markdown by the platform if it supports it.

### `Sleep`

This layer creates a pause between two messages. The duration is
indicated in seconds.

```python
class FakeState(FakeAppState):
    async def handle(self):
        """
        Sends FOO then BAR with a 0.5s pause in between.
        """

        self.send(lyr.Text(t.FOO))
        self.send(lyr.Sleep(0.5))
        self.send(lyr.Text(t.BAR))
```

## `Postback`

When platforms allow to have buttons, usually they allow to send a
specific payload when the user click it. This payload comes back as a
`Postback` layer. No platform support sending a `Postback`, it's only
meant to be received.

```python
class FakeState(FakeAppState):
    async def handle(self):
        payload = self.request.get_layer(lyr.Postback).payload

        if payload['action'] == 'foo':
            self.send(lyr.Text(t.FOO))
        elif payload['action'] == 'bar':
            self.send(lyr.Text(t.BAR))
```

## `Image`, `Audio`, `File` and `Video`

They are the media layer. They will have a `media` attribute which is
a `BaseMedia` object and allows you to send or receive a media file.
Please note that the media API is still a work in progress.

```python
class FakeState(FakeAppState):
    async def handle(self):
        self.send(lyr.Image(UrlMedia('https://domain/image.jpg')))
```

## `Location`

That layer holds a point in space, with a longitude and a latitude.

```python
class FakeState(FakeAppState):
    async def handle(self):
        self.send(lyr.Location(
            lyr.Location.Point(lon=0, lat=0),
        ))
```

## `Message`

The `Message` layer contains another message, from which you can read
the stack.

## `Typing`

Indicates to the platform that the bot is currently "typing" or stopped
typing. This is automatically inserted by the `AutoType` middleware.
