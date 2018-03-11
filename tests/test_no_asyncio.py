import functools
import asyncio
import no_asyncio

def start_loop(func):
    """
    Wrapper for starting a loop to avoid needing multiple functions to start
    the main function.
    """
    @functools.wraps(func)
    def new_func(*args, **kwargs):
        asyncio.get_event_loop().run_until_complete(func())

    return new_func

class NoAsyncioExample(metaclass=no_asyncio.NoAsync):
    magic = ['no_async', 'another_magic']

    def no_async_test(self, index):
        """
        Rewritten because it starts with a magic string.
        """
        return self.do(index)

    def async_func(self):
        """
        Should be rewritten because it calls no_async_test()
        """
        return self.no_async_test(4)

    async def do(self, index):
        return index

    def another_magic_string(self):
        """
        Rewritten because it starts with a magic string.
        """
        return self.do(7)

@start_loop
async def test_no_asyncio():
    t = NoAsyncioExample()

    result = await t.no_async_test(5)
    assert result == 5

    result = await t.async_func()
    assert result == 4

    result = await t.another_magic_string()
    assert result == 7
