import logging
import os.path
import sys

import ply.yacc
from jsonpath_ng.exceptions import JsonPathParserError
from jsonpath_ng.jsonpath import *
from jsonpath_ng.lexer import JsonPathLexer

logger = logging.getLogger(__name__)


def parse(string):
    return JsonPathParser().parse(string)


class JsonPathParser:
    """
    An LALR-parser for JsonPath
    """

    tokens = JsonPathLexer.tokens

    def __init__(self, debug=False, lexer_class=None):
        if self.__doc__ is None:
            raise JsonPathParserError(
                "Docstrings have been removed! By design of PLY, "
                "jsonpath-rw requires docstrings. You must not use "
                "PYTHONOPTIMIZE=2 or python -OO."
            )

        self.debug = debug
        self.lexer_class = (
            lexer_class or JsonPathLexer
        )  # Crufty but works around statefulness in PLY

        # Since PLY has some crufty aspects and dumps files, we try to keep them local
        # However, we need to derive the name of the output Python file :-/
        output_directory = os.path.dirname(__file__)
        try:
            module_name = os.path.splitext(os.path.split(__file__)[1])[0]
        except:
            module_name = __name__

        start_symbol = "jsonpath"
        parsing_table_module = "_".join([module_name, start_symbol, "parsetab"])

        # Generate the parse table
        self.parser = ply.yacc.yacc(
            module=self,
            debug=self.debug,
            tabmodule=parsing_table_module,
            outputdir=output_directory,
            write_tables=0,
            start=start_symbol,
            errorlog=logger,
        )

    def parse(self, string, lexer=None):
        lexer = lexer or self.lexer_class()
        return self.parse_token_stream(lexer.tokenize(string))

    def parse_token_stream(self, token_iterator):
        return self.parser.parse(lexer=IteratorToTokenStream(token_iterator))

    # ===================== PLY Parser specification =====================

    precedence = [
        ("left", ","),
        ("left", "DOUBLEDOT"),
        ("left", "."),
        ("left", "|"),
        ("left", "&"),
        ("left", "WHERE"),
        ("left", "WHERENOT"),
    ]

    def p_error(self, t):
        if t is None:
            raise JsonPathParserError("Parse error near the end of string!")
        raise JsonPathParserError(
            "Parse error at %s:%s near token %s (%s)" % (t.lineno, t.col, t.value, t.type)
        )

    def p_jsonpath_binop(self, p):
        """jsonpath : jsonpath '.' jsonpath
        | jsonpath DOUBLEDOT jsonpath
        | jsonpath WHERE jsonpath
        | jsonpath WHERENOT jsonpath
        | jsonpath '|' jsonpath
        | jsonpath '&' jsonpath"""
        op = p[2]

        if op == ".":
            p[0] = Child(p[1], p[3])
        elif op == "..":
            p[0] = Descendants(p[1], p[3])
        elif op == "where":
            p[0] = Where(p[1], p[3])
        elif op == "wherenot":
            p[0] = WhereNot(p[1], p[3])
        elif op == "|":
            p[0] = Union(p[1], p[3])
        elif op == "&":
            p[0] = Intersect(p[1], p[3])

    def p_jsonpath_fields(self, p):
        "jsonpath : fields_or_any"
        p[0] = Fields(*p[1])

    def p_jsonpath_named_operator(self, p):
        "jsonpath : NAMED_OPERATOR"
        if p[1] == "this":
            p[0] = This()
        elif p[1] == "parent":
            p[0] = Parent()
        else:
            raise JsonPathParserError(
                "Unknown named operator `%s` at %s:%s" % (p[1], p.lineno(1), p.lexpos(1))
            )

    def p_jsonpath_root(self, p):
        "jsonpath : '$'"
        p[0] = Root()

    def p_jsonpath_idx(self, p):
        "jsonpath : '[' idx ']'"
        p[0] = p[2]

    def p_jsonpath_slice(self, p):
        "jsonpath : '[' slice ']'"
        p[0] = p[2]

    def p_jsonpath_fieldbrackets(self, p):
        "jsonpath : '[' fields ']'"
        p[0] = Fields(*p[2])

    def p_jsonpath_child_fieldbrackets(self, p):
        "jsonpath : jsonpath '[' fields ']'"
        p[0] = Child(p[1], Fields(*p[3]))

    def p_jsonpath_child_idxbrackets(self, p):
        "jsonpath : jsonpath '[' idx ']'"
        p[0] = Child(p[1], p[3])

    def p_jsonpath_child_slicebrackets(self, p):
        "jsonpath : jsonpath '[' slice ']'"
        p[0] = Child(p[1], p[3])

    def p_jsonpath_parens(self, p):
        "jsonpath : '(' jsonpath ')'"
        p[0] = p[2]

    # Because fields in brackets cannot be '*' - that is reserved for array indices
    def p_fields_or_any(self, p):
        """fields_or_any : fields
        | '*'
        | NUMBER"""
        if p[1] == "*":
            p[0] = ["*"]
        elif isinstance(p[1], int):
            p[0] = str(p[1])
        else:
            p[0] = p[1]

    def p_fields_id(self, p):
        "fields : ID"
        p[0] = [p[1]]

    def p_fields_comma(self, p):
        "fields : fields ',' fields"
        p[0] = p[1] + p[3]

    def p_idx(self, p):
        "idx : NUMBER"
        p[0] = Index(p[1])

    def p_slice_any(self, p):
        "slice : '*'"
        p[0] = Slice()

    def p_slice(self, p):  # Currently does not support `step`
        """slice : maybe_int ':' maybe_int
        | maybe_int ':' maybe_int ':' maybe_int"""
        p[0] = Slice(*p[1::2])

    def p_maybe_int(self, p):
        """maybe_int : NUMBER
        | empty"""
        p[0] = p[1]

    def p_empty(self, p):
        "empty :"
        p[0] = None


class IteratorToTokenStream:
    def __init__(self, iterator):
        self.iterator = iterator

    def token(self):
        try:
            return next(self.iterator)
        except StopIteration:
            return None


if __name__ == "__main__":
    logging.basicConfig()
    parser = JsonPathParser(debug=True)
    print(parser.parse(sys.stdin.read()))
