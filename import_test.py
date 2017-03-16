import asyncio
import no_asyncio

class MyTest(metaclass=no_asyncio.NoAsync):
    magic = 'head'

    def __init__(self):
        self.session = uvhttp.http.Session(10, loop=asyncio.get_event_loop())

    def test_hi(self):
        response = self.session.head(b'http://127.0.0.1/')
        print(response.status_code)

@no_asyncio.start_loop
async def main():
    t = no_asyncio.Test()
    task = asyncio.ensure_future(t.test_async_func())
    task2 = asyncio.ensure_future(t.test_async_func())
    task3 = asyncio.ensure_future(t.test_lol())

    await asyncio.wait([task, task2, task3])

    m = MyTest()
    await m.test_hi()

if __name__ == '__main__':
    try:
        __importing__
    except NameError:
        main()
