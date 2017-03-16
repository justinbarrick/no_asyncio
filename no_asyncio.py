import asyncio
import functools
import uvhttp.http
import inspect
import ast

class RewriteAST(ast.NodeTransformer):
    """
    Rewrite the AST to replace all functions that start with test_ with async
    functions and all calls to the provided magic string *.magic*() and
    magic*() with awaits.
    """

    def __init__(self, magic):
        self.magic = magic

    def is_magic_call(self, node):
        if not isinstance(node, ast.Call):
            return False
        elif not isinstance(node.func, ast.Name) and not isinstance(node.func, ast.Attribute):
            return False
        elif isinstance(node.func, ast.Name) and not node.func.id.startswith(self.magic):
            return False
        elif isinstance(node.func, ast.Attribute) and not node.func.attr.startswith(self.magic):
            return False

        return True

    def visit_FunctionDef(self, node):
        # Ignore special functions like __init__
        if node.name.startswith('__') and node.name.endswith('__'):
            return node

        magic = False

        for child in ast.walk(node):
            if self.is_magic_call(child):
                magic = True
                break

        if not magic:
            return node

        node = ast.copy_location(ast.AsyncFunctionDef(name=node.name,
            args=node.args, body=node.body, decorator_list=node.decorator_list,
            returns=node.returns), node)
        node = self.generic_visit(node)
        return node

    def visit_Call(self, node):
        if self.is_magic_call(node):
            return ast.copy_location(ast.Await(value=node), node)
        return node

class NoAsync(type):
    """
    Metaclass that automatically converts methods that call functions matching
    the magic name (self.magic) to async functions and awaits on the magic
    functions.

    As it is a metaclass, the methods are rewritten when the class is first
    defined.
    """
    def __new__(cls, name, bases, namespace):
        # make sure we aren't already importing
        try:
            __importing__
            return type.__new__(cls, name, bases, namespace)
        except NameError:
            pass

        try:
            # Fetch __importing__ from the calling scope in case it's
            # different.
            inspect.stack()[1][0].f_globals['__importing__']
            return type.__new__(cls, name, bases, namespace)
        except KeyError:
            pass

        # Get the file containing the class from the stack.
        code_file = inspect.stack()[1].filename
        tree = ast.parse(open(code_file).read())
        tree = RewriteAST(namespace.get('magic', 'do')).visit(tree)
        tree = ast.fix_missing_locations(tree)

        def compile_context():
            # Set __importing__ to True in the import scope.
            g = globals().copy()
            g['__importing__'] = True

            # Compile and execute the execute the AST return its scope.
            compiled = compile(tree, code_file, 'exec')
            exec(compiled, g)

            # Return the scope.
            return g

        # Update the class's scope with the imported class.
        namespace.update(compile_context()[name].__dict__)
        return type.__new__(cls, name, bases, namespace)

def start_loop(func):
    """
    Wrapper for starting a loop to avoid needing multiple functions to start
    the main function.
    """
    @functools.wraps(func)
    def new_func(*args, **kwargs):
        asyncio.get_event_loop().run_until_complete(func())

    return new_func

class Test(metaclass=NoAsync):
    def __init__(self):
        self.session = uvhttp.http.Session(10, loop=asyncio.get_event_loop())

    def test_lol(self):
        self.do()

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

@start_loop
async def main():
    t = Test()

    # Make two requests at once.
    task = asyncio.ensure_future(t.test_async_func())
    task2 = asyncio.ensure_future(t.test_async_func())
    task3 = asyncio.ensure_future(t.test_lol())

    await asyncio.wait([task, task2, task3])

if __name__ == '__main__':
    try:
        __importing__
    except NameError:
        main()
