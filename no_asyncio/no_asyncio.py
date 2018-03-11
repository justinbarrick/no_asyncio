import inspect
import ast

class RewriteAST(ast.NodeTransformer):
    """
    Rewrite the AST to replace all functions that call the magic async
    functions and all calls to the provided magic string *.magic*() and
    magic*() with awaits.
    """

    def __init__(self, magic):
        self.magic = magic

    def starts_with_magic(self, name):
        for magic in self.magic:
            if name.startswith(magic):
                return True
        return False

    def is_magic_call(self, node):
        if not isinstance(node, ast.Call):
            return False
        elif not isinstance(node.func, ast.Name) and not isinstance(node.func, ast.Attribute):
            return False
        elif isinstance(node.func, ast.Name) and not self.starts_with_magic(node.func.id):
            return False
        elif isinstance(node.func, ast.Attribute) and not self.starts_with_magic(node.func.attr):
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
