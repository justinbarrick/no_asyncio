Demonstrates rewriting the Python AST so that async functions can be
transparently called and written.

# Installation

Add the package:

```
pip install no_asyncio
```

You can now include it in your project to transparently rewrite any methods to
transparently be async.

# Examples

See the examples for a working demo.

`no_asyncio` provides a metaclass that will automatically rewrite methods
that call any function matching a magic string pattern to async functions.

This code:

```
class MyExample(metaclass=no_asyncio.NoAsync):
    magic = ['head']

    def __init__(self):
        self.session = uvhttp.http.Session(10, loop=asyncio.get_event_loop())

    def do_request(self):
        response = self.session.head(b'http://127.0.0.1/')
        print(response.status_code)
```

Becomes rewritten to the following at runtime:

```
class MyExample(metaclass=no_asyncio.NoAsync):
    magic = 'head'

    def __init__(self):
        self.session = uvhttp.http.Session(10, loop=asyncio.get_event_loop())

    async def do_request(self):
        response = await self.session.head(b'http://127.0.0.1/')
        print(response.status_code)
```
