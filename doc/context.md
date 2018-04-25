Context
=======

In BERNARD, the context is a short-lived storage that allows to store
temporary information, like the user's filters in his current session.

There is only one default implementation, based on Redis, but you can
easily provide yours as long as you can implement the `BaseContextStore`
interface.

## Usage

To create a context store, create a `store.py` file with the following
content:

```python
from bernard.storage.context import (
    create_context_store,
)

cs = create_context_store()
```

Then you can use it from any state using the `@cs.inject()` decorator
and adding a `context` argument to your handler.

```python
class SomeState(MyAppState):
    @cs.inject()
    async def handle(self, context) -> None:
        context['number'] = random.randint(1, 100)
```

The same technique can also be used on any custom trigger.

Once you leave the state, the context is automatically serialized
(usually in JSON) and saved to the store.

## Configuration

By default, BERNARD expects a `REDIS_URL` which will indicate the
address of your Redis server in the format

```bash
REDIS_URL=redis://10.0.0.1/0
```

If you do not want to use this environment variable to configure Redis,
you can override the settings:

```python
CONTEXT_STORE = {
    'class': 'bernard.storage.context.RedisContextStore',
    'params': {
        'host': 'localhost',
        'port': 6379,
        'db_id': 0,
    },
}
```

You can also change the `class` if you want to provide your own
implementation.

## Reference

### create_context_store()

It accepts 3 arguments:

- `name` indicates the name of your context store. If you want to use
  several context stores (by example, if you want different TTLs), you
  **NEED** to set different names for all your contexts, otherwise
  they'll override each other all over.
- `ttl` is the time to live in seconds of the context. When the context
  is deleted, it is deleted completely at once. The TTL is reset every
  time that the context is modified.
- `store` storage configuration. Defaults to `settings.CONTEXT_STORE`.

### `BaseContextStore.inject()`

This is a decorator that will read the context when entering the
decorated function and save it back when leaving it. It expects to be
decorating an object method and that the object has a `self.request`
attribute. So basically, it expects either to decorate a state handler
or a trigger's ranker.

```python
    def inject(self,
               require: Optional[Text] = None,
               fail: Text = 'missing_context',
               var_name: Text = 'context'):
```

Options:

- `require`: require a specific list of keys to be present in the
  context. If they can't be found, then the `fail` function is called.
- `fail`: name of the method to call in case of a missing key
- `var_name`: name of the parameter in the handler's arguments. This is
  useful to inject several contexts at once

Example:

```python
cs1 = create_context_store(name='context_1')
cs2 = create_context_store(name='context_2', ttl=0)

class SomeState(MyAppState):
    @cs1.inject(var_name='context_1')
    @cs2.inject(var_name='context_2')
    async def handle(self, context_1, context_2) -> None:
        context_1['number'] = random.randint(1, 100)
        context_2['some_stuff'] = 'this context does not expire'
```
