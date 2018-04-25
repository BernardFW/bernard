Triggers
========

While you can pretty easily provide your own trigger, there is a few
triggers that are built into the framework to make your life easier.
They will help you solve the most basic problems.

## Built-in triggers

All triggers can be found in `bernard.engine.triggers`.

### `Anything`

That's a trigger that is **always** activated. Usually used to make
an automatic jump between two states.

```python
# ...

Tr(dest=State1, factory=trg.Action.builder('get_started')),
Tr(dest=State2, origin=State1, factory=trg.Anything()),

# ...
```

### `Text`

Detects a specfic NLU intent using the
[built-in NLU engine](./lang/nlu.md). Supposing that you defined a
`GET_STARTED` intent:

```python
Tr(dest=State1, factory=trg.Text.builder(its.GET_STARTED)),
```

### `Choice`

Some layers allow the user to make choices, aka Facebook's
`QuickRepliesList` and Telegram's `ReplyKeyboard`.

In those cases, each button will be associated to both a `slug` and
optionally to an `intent`. If the user clicks the button or the user
says something that triggers the intent, it will be picked up by the
`Choice` layer. You can have a look at the "Branch"
[pattern](./pattern.md).

```python
Tr(dest=State2, origin=State1, factory=trg.Choice.builder('do_stuff'))
```

If you want to know which choice was made from the handler, you should
always get it through the trigger:

```python
class FakeState(MyAppState):
    async def handle(self):
        assert isinstance(self.trigger, trg.Choice)
        choice = self.trigger.slug

        # ...
```

### `Action`

The `Action` trigger will look into any `Postback` layer that have a
dictionary payload if there is an `action` key.

Suppose you have the following layer:

```
# ...
tgr.InlineKeyboard([[
    tgr.InlineKeyboardCallbackButton(
        text='Click me',
        payload={
            'action': 'click',
        },
    ),
]]),
# ...
```

You can catch its clicks with

```python
# ...
    Tr(
        dest=SomeState,
        factory=trg.Action.builder('click'),
    ),
# ...
```

This works at least with:

- Facebook's persistent menu
- Facebook's buttons (on button or generic template)
- Telegram's inline keyboards

You should also use this technique when sending a manual postback
through `bernard.js`, by example

```javascript
bernard.sendPostack(token, {
    action: 'do_stuff',
    item: 42,
});
```

### `Layer`

This trigger will activate if a certain type of layer is found. Useful
when you expect something specific, like the user's location:

```python
Tr(dest=ShowPlaces, factory=trg.Layer.builder(lyr.Location)),
```

### `Worst`

Runs several other triggers and takes the lowest score. This is the
roughly equivalent of a logical `AND`.

This is useful if you create a custom trigger that serves as a branching
condition.

Suppose that you have a `IsUserRegistered` trigger that allows you to
know if the user is registered:

```python
# Activates when the user is registered
IsUserRegistered.builder(True)

# Activates when the user is not registered
IsUserRegistered.builder(False)
```

Using this, you can combine it with another layer:

```python
# Activates when the user sends his location AND is registered
Tr(
    dest=SomeStuff,
    factory=trg.Worst.builder([
        trg.Layer.builder(lyr.Location),
        IsUserRegistered.builder(True),
    ]),
),

# Activates when the user sends his location AND is not registered
Tr(
    dest=TellUserToRegister,
    factory=trg.Worst.builder([
        trg.Layer.builder(lyr.Location),
        IsUserRegistered.builder(False),
    ]),
),
```

### `Equal`

Tests the exact equality of received layer with a static layer. This is
useful to detect Telegram's bot commands:

```python
# ...
Tr(
    dest=TestState,
    factory=trg.Equal.builder(BotCommand('/test')),
),
# ...
```

## Custom trigger

When you integrate to external APIs or services, creating your own
trigger quickly becomes an important need. Fortunately, it's pretty
simple to create your own trigger.

To do so, there is two interfaces youc an implement:

- `BaseTrigger` if you do static computations
- `SharedTrigger` if you need to call an API

More details in the following sections

### `BaseTrigger`

Here is a template for a static trigger

```python
class SomeTrigger(BaseTrigger):
    def __init__(self, request: Request, some_param: Any) -> None:
        super().__init__(request)
        self.some_param = some_param

    def rank() -> Optional[float]:
        # TODO implement this function
```

Regarding the constructor there is only one rule: your first argument
needs to be `request` and you need to call `super()`.

Then comes the `rank()` function. It can either be static either be
`async`. It's expected to return either `None` either a number between
`0.0` and `1.0` (included). Consider it as a probability: the closest
you are to `1.0` the surer you are that the current message is good
for you.

You can simply access the current request using `self.request`.

### `SharedTrigger`

One specificity of the triggers system is that all candidate triggers
are called in parallel (which can be a lot of triggers at once if you're
not careful!). The consequence is that if you make the same call in
several triggers, the call might go several times at once, which isn't
helpful and could even cause race conditions in your API.

For this reason exists the `SahredTrigger`. It allows you to share an
API call between several instances of the same trigger.

Here's a template

```python
class SomeSharedTrigger(SharedTrigger):
    async def call_api(self) -> Any:
        return await make_your_api_call()

    async def compute_rank(self, value) -> Optional[flaot]:
        # `value` is the output of make_your_api_call()
        # TODO make something with it and return a value between 0 and 1
```

In this interface, you call the API in `call_api()` which will only be
called once. Then the output of `call_api()` will be passed as `value`
to `compute_rank(value)` of all instances.
