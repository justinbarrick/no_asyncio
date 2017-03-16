import asyncio
import functools
import uvhttp.http
import ast

class RewriteAST(ast.NodeTransformer):
    """
    Rewrite the AST to replace all functions that start with test_ with async
    functions and all calls to *.do() and do() with awaits.
    """

    def visit_FunctionDef(self, node):
        if not node.name.startswith('test'):
            return node

        node = ast.copy_location(ast.AsyncFunctionDef(name=node.name,
            args=node.args, body=node.body, decorator_list=node.decorator_list,
            returns=node.returns), node)
        node = RewriteAST().visit(node)
        return node

    def visit_Call(self, node):
        """
        Note: in the current implementation, awaiting on the magic function
        won't work. Recursing the tree would be better.
        """
        if not isinstance(node.func, ast.Name) and not isinstance(node.func, ast.Attribute):
            return node
        elif isinstance(node.func, ast.Name) and node.func.id != 'do':
            return node
        elif isinstance(node.func, ast.Attribute) and node.func.attr != 'do':
            return node

        return ast.copy_location(ast.Await(value=node), node)

def rewrite_ast():
    """
    Load the current file and rewrite globals with the new AST.

    This should be changed to an import() function for importing modules.
    """
    global __name__
    __name__ = '__notmain__'

    tree = ast.parse(open(__file__).read())
    tree = RewriteAST().visit(tree)
    tree = ast.fix_missing_locations(tree)
    exec(compile(tree, __file__, 'exec'), globals())

def start_loop(func):
    """
    Wrapper for starting a loop to avoid needing multiple functions to start
    the main function.
    """
    @functools.wraps(func)
    def new_func(*args, **kwargs):
        asyncio.get_event_loop().run_until_complete(func())

    return new_func

@start_loop
async def main():
    t = Test()

    # Make two requests at once.
    task = asyncio.ensure_future(t.test_async_func())
    task2 = asyncio.ensure_future(t.test_async_func())

    await asyncio.wait([task, task2])

class Test:
    def __init__(self):
        self.session = uvhttp.http.Session(10, loop=asyncio.get_event_loop())

    def test_async_func(self):
        """
        This example function will be rewritten to an async function that will
        await on self.do()
        """
        for _ in range(10):
            t = self.do()
            print(t.status_code)

    async def do(self):
        return await self.session.get(b'http://127.0.0.1/')

if __name__ == '__main__':
    rewrite_ast()
    main()
