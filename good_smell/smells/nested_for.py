from good_smell import AstSmell, LoggingTransformer
import ast


class NameInNode(LoggingTransformer):
    def __init__(self, name: ast.Name):
        self.name = name
        super().__init__()

    def is_smelly(self, node: ast.AST) -> bool:
        return isinstance(node, ast.Name) and node.id == self.name.id


def name_in_node(node: ast.AST, name: ast.Name) -> bool:
    """Checks if the node `name` is in `node`"""
    checker = NameInNode(name)
    checker.visit(node)
    return bool(checker.transformed_nodes)


class NestedFor(AstSmell):
    """Checks for adjacent nested fors and replaces them with itertools.product"""

    @property
    def transformer_class(self):
        return NestedForTransformer

    @property
    def warning_message(self):
        return "Consider using itertools.product instead of a nested for"

    @property
    def symbol(self):
        return "nested-for"


class NestedForTransformer(LoggingTransformer):
    """NodeTransformer that goes visits all the nested `for`s and replaces them
    with itertools.product"""

    def visit_For(self, node: ast.For) -> ast.For:
        inner_for: ast.For = node.body[0]
        import_itertools = ast_node("import itertools")
        itertools_product = ast_node("itertools.product").value
        new_for = ast.For(
            target=ast.Tuple(elts=[node.target, inner_for.target]),
            iter=ast.Call(
                func=itertools_product, args=[node.iter, inner_for.iter], keywords=[]
            ),
            body=inner_for.body,
            orelse=node.orelse,
        )
        new_for = ast.fix_missing_locations(new_for)
        return [ast.copy_location(import_itertools, node), new_for]

    @staticmethod
    def is_smelly(node: ast.AST):
        """Check if the node is only a nested for"""
        return (
            isinstance(node, ast.For)
            and isinstance(node.body[0], ast.For)
            and len(node.body) == 1
            # Check there's no dependancy between nodes
            and not name_in_node(node.body[0].iter, node.target)
        )


def ast_node(expr: str) -> ast.AST:
    """Helper function to parse a string denoting an expression into an AST node"""
    # ast.parse returns "Module(body=[Node])"
    return ast.parse(expr).body[0]
