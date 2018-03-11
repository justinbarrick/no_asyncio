import uvhttp.http
import asyncio
import logging
import no_asyncio

class HTTPExample(metaclass=no_asyncio.NoAsync):
    magic = ['get', 'head']

    def __init__(self):
        self.session = uvhttp.http.Session(10, loop=asyncio.get_event_loop())

    def fetch_google(self):
        response = self.session.head(b'http://google.com/')
        return response.status_code

    def retrieve_google(self):
        response = self.session.get(b'http://google.com/')
        return response.status_code

async def main():
    example = HTTPExample()

    request_1 = await example.fetch_google()
    logging.error('HEAD: {}'.format(request_1))

    request_2 = await example.retrieve_google()
    logging.error('HEAD: {}'.format(request_2))

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
