# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from sexpdata import (
    PY3,
    ExpectClosingBracket, ExpectNothing, ExpectSExp,
    parse, tosexp, Symbol, String, Quoted, bracket, Parens,
    Brackets, Delimiters,
)
import unittest

import pytest


### Test cases

data_identity = [
    Symbol('a'),
    'a',
    [Symbol('a')],
    ['a'],
    Quoted(Symbol('a')),
    Quoted('a'),
    Quoted([Symbol('a')]),
    Quoted(['a']),
    [Symbol('a'), Symbol('b')],
    [Symbol('a'), [Symbol('b')]],
    [Symbol('a'), Quoted([Symbol('b')])],
    [Symbol('a'), Quoted(Symbol('b')), Symbol('c')],
    [Symbol('a'), Quoted([Symbol('b')]), Symbol('c')],
    [Symbol('a'), Quoted(Symbol('b')), Quoted(Symbol('c')), Symbol('d')],
    [Symbol('a'), Quoted(Symbol('b')), Symbol('c'), Quoted(Symbol('d'))],
    [Symbol('set'), Symbol("set\'")],
    [bracket([1, 2, 3], '[')],
    [bracket([1, [2, bracket([3], '[')]], '[')],
    '""',
    "",
    "''",
    "'",
    '\\',
    '\\\"',
    ";",
    Symbol(r'path.join'),
    Symbol(r'path join'),
    Symbol(r'path\join'),
    "日本語能力!!ソﾊﾝｶｸ",
]

data_identity += map(lambda x: x[0], String._lisp_quoted_specials)
data_identity += map(lambda x: x[1], String._lisp_quoted_specials)


def test_identity():
    for data in data_identity:
        assert parse(tosexp(data))[0] == data


def test_identity_pretty_print():
    for data in data_identity:
        assert parse(tosexp(data, pretty_print=True))[0] == data


class BaseTestCase(unittest.TestCase):

    def assert_parse(self, string, obj):
        """`string` must be parsed into `obj`."""
        self.assertEqual(parse(string)[0], obj)


class TestSymbol(BaseTestCase):

    def test_parse_symbol_with_backslash(self):
        self.assert_parse(r'path.join', Symbol(r'path.join'))
        self.assert_parse(r'path\ join', Symbol(r'path join'))
        self.assert_parse(r'path\\join', Symbol(r'path\join'))

    def test_parse_special_symbols(self):
        for s in [r'\\', r"\'", r"\`", r'\"', r'\(', r'\)', r'\[', r'\]',
                  r'\ ', r'\.', r'\,', r'\?', r'\;', r'\#']:
            self.assert_parse(s, Symbol(Symbol.unquote(s)))

    def test_hashable_and_distinct(self):
        d = {
            String("A"): "StrA",
            Symbol("A"): "SymA",
            "A": "strA",
        }
        self.assertEqual(3, len(d))
        self.assertEqual("StrA", d[String("A")])
        self.assertEqual("SymA", d[Symbol("A")])
        self.assertEqual("strA", d["A"])


class TestParseFluctuation(BaseTestCase):

    def test_spaces_must_be_ignored(self):
        self.assert_parse(' \n\t\r  ( ( a )  \t\n\r  ( b ) )  ',
                          [[Symbol('a')], [Symbol('b')]])

    def test_spaces_between_parentheses_can_be_skipped(self):
        self.assert_parse('((a)(b))', [[Symbol('a')], [Symbol('b')]])

    def test_spaces_between_double_quotes_can_be_skipped(self):
        self.assert_parse('("a""b")', ['a', 'b'])

class TestDeliminter(BaseTestCase):

    def test_normal(self):
        """
        When the brace subclass does not exist, brace should be parsed as alphanumeric
        """
        import gc
        gc.collect()
        self.assertEqual(Delimiters.get_brackets(), {"(": ")", "[": "]"})
        self.assertEqual(parse('{a b c}'), [Symbol("{a"), Symbol("b"), Symbol("c}")])

    def test_curly_brace(self):
        """
        Extending the delimiters using braces
        """
        class Braces(Delimiters):
            opener, closer = '{', '}'

        self.assertEqual(Delimiters.get_brackets(), {"(": ")", "[": "]", "{": "}"})

        self.assert_parse('[a b c]', Brackets([Symbol("a"), Symbol("b"), Symbol("c")]))
        self.assert_parse('{a b c}', Braces([Symbol("a"), Symbol("b"), Symbol("c")]))
    def test_multiple_brackets(self):
        """
        Extending the delimiters using braces and unicode braces
        """
        class Implicit(Delimiters):
            opener, closer = '{', '}'
        class StrictImplicit(Delimiters):
            opener, closer = '⦃', '⦄'

        target = "{σ : Type u} → {m : Type u → Type v} → [inst : Functor m] → ⦃α : Type u⦄ → StateT σ m α → σ → m α"
        self.assertEqual(Delimiters.get_brackets(), {"(": ")", "[": "]", "{": "}", '⦃': '⦄'})

        self.assertEqual(parse(target), [
            Implicit([Symbol('σ'), Symbol(':'), Symbol('Type'), Symbol('u')]),
            Symbol('→'),
            Implicit([Symbol('m'), Symbol(':'), Symbol('Type'), Symbol('u'), Symbol('→'), Symbol('Type'), Symbol('v')]),
            Symbol('→'),
            Brackets([Symbol('inst'), Symbol(':'), Symbol('Functor'), Symbol('m')]),
            Symbol('→'),
            StrictImplicit([Symbol('α'), Symbol(':'), Symbol('Type'), Symbol('u')]),
            Symbol('→'),
            Symbol('StateT'), Symbol('σ'), Symbol('m'), Symbol('α'),
            Symbol('→'),
            Symbol('σ'), Symbol('→'), Symbol('m'), Symbol('α')
        ])

class TestUnicode(BaseTestCase):

    ustr = "日本語能力!!ソﾊﾝｶｸ"

#    if not PY3:
        # Let's not support dumping/parsing bytes.
        # (In Python 3, ``string.encode()`` returns bytes.)

    def test_dump_raw_utf8(self):
        """
        Test that sexpdata supports dumping encoded (raw) string.

        See also: https://github.com/tkf/emacs-jedi/issues/43

        """
        ustr = self.ustr
        sexp = '"{0}"'.format(ustr)
        self.assertEqual(tosexp(ustr), sexp)

    def test_parse_raw_utf8(self):
        ustr = self.ustr
        sexp = '"{0}"'.format(ustr)
        self.assert_parse(sexp, ustr)


def test_tosexp_str_as():
    assert tosexp('a', str_as='symbol') == 'a'
    assert tosexp(['a'], str_as='symbol') == '(a)'
    assert tosexp('a') == '"a"'
    assert tosexp(['a']) == '("a")'
    assert tosexp(Quoted('a')) == '\'"a"'
    assert tosexp(Quoted(['a']), str_as='symbol') == '\'(a)'
    assert tosexp([Quoted('a')], str_as='symbol') == '(\'a)'
    assert tosexp(Quoted('a'), str_as='symbol') == '\'a'
    assert tosexp(Quoted(['a'])) == '\'("a")'
    assert tosexp([Quoted('a')]) == '(\'"a")'


def test_tosexp_tuple_as():
    assert tosexp(('a', 'b')) == '("a" "b")'
    assert tosexp(('a', 'b'), tuple_as='array') == '["a" "b"]'
    assert tosexp([('a', 'b')]) == '(("a" "b"))'
    assert tosexp([('a', 'b')], tuple_as='array') == '(["a" "b"])'
    assert tosexp(Quoted(('a',))) == '\'("a")'
    assert tosexp(Quoted(('a',)), tuple_as='array') == '\'["a"]'


def test_tosexp_value_errors():
    with pytest.raises(ValueError):
        tosexp((), tuple_as='')
    with pytest.raises(ValueError):
        tosexp('', str_as='')
    with pytest.raises(ValueError):
        tosexp(Parens())


def test_parse_float():
    assert parse("-1.012") == [-1.012]
    assert parse("2E22") == [Symbol("2E22")]
    assert parse("inf") == [Symbol("inf")]


def test_too_many_brackets():
    with pytest.raises(ExpectNothing):
        parse("(a b))")


def test_not_enough_brackets():
    with pytest.raises(ExpectClosingBracket):
        parse("(a (b)")


def test_no_eol_after_comment():
    assert parse('a ; comment') == [Symbol('a')]


def test_issue_4():
    assert parse("(0 ;; (\n)") == [[0]]
    assert parse("(0;; (\n)") == [[0]]


def test_issue_18():
    import sexpdata
    sexp = "(foo)'   "
    with pytest.raises(ExpectSExp, match='No s-exp is found after an '
                                         'apostrophe at position 5'):
        sexpdata.parse(sexp)

    sexp = "'   "
    with pytest.raises(ExpectSExp, match='No s-exp is found after an '
                                         'apostrophe at position 0'):
        sexpdata.parse(sexp)


def test_other_issue_18():
    import sexpdata
    sexp = b"(foo)'   "
    with pytest.raises(AssertionError):
        sexpdata.loads(sexp)


def test_issue_37_value_field():
    assert String('ObjStr').value() == 'ObjStr'
    assert Symbol('ObjSym').value() == 'ObjSym'
    assert Symbol('ObjList').value() == 'ObjList'
