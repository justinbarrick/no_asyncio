import asyncio
import functools
import types
import concurrent.futures
import uvhttp.http
import ast
import json

def start_loop(func):
    @functools.wraps(func)
    def new_func(*args, **kwargs):
        asyncio.get_event_loop().run_until_complete(func())

    return new_func

class RewriteAST(ast.NodeTransformer):
    def visit_FunctionDef(self, node):
        if not node.name.startswith('test'):
            return node

        node = ast.copy_location(ast.AsyncFunctionDef(name=node.name,
            args=node.args, body=node.body, decorator_list=node.decorator_list,
            returns=node.returns), node)
        node = RewriteAST().visit(node)
        return node

    def visit_Call(self, node):
        if not isinstance(node.func, ast.Name):
            return node
           
        if node.func.id != 'do':
            return node

        node = ast.copy_location(ast.Await(value=node), node)
        return node

def rewrite_ast():
    global __name__
    __name__ = '__notmain__'

    tree = ast.parse(open(__file__).read())
    tree = RewriteAST().visit(tree)
    tree = ast.fix_missing_locations(tree)
    exec(compile(tree, __file__, 'exec'), globals())

@start_loop
async def main():
    t = Test()

    task = asyncio.ensure_future(t.test_async_func())
    task2 = asyncio.ensure_future(t.test_async_func())

    await asyncio.wait([task, task2])


async def do(session):
    return await session.get(b'http://127.0.0.1/')

class Test:
    def __init__(self):
        self.session = uvhttp.http.Session(10, loop=asyncio.get_event_loop())

    def test_async_func(self):
        for _ in range(10):
            t = do(self.session)
            print(t.status_code)

if __name__ == '__main__':
    rewrite_ast()
    main()
