Middlewares
===========

Middlewares allow to easily hookup to different places in a messages handling
lifecycle. This document describes the available events.

## Events

### `pre_handle`

```
pre_handle(request: Request, responder: Responder)
```

Called before all the handling logic happened (before triggering the triggers
and so on), but inside the message handling lock.

### `flush`

```
flush(request: 'Request', stacks: List[Stack])
```

That's when messages are being flushed to the platform. This is an opportunity
to alter the stack to your liking.
