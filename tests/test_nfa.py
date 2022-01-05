from typing import Tuple
from re2py import re2post, post2nfa, match
import pytest


@pytest.mark.parametrize(
    ("re", "post"),
    [
        ("a", "a"),
        ("(a)", "a"),
        ("ab", "ab."),
        ("a*", "a*"),
        ("a+", "a+"),
        ("a?", "a?"),
        ("a|b", "ab|"),
        ("a(b|c)", "abc|."),
        ("ab|c", "ab.c|"),
        ("a(bb)+a", "abb.+.a."),
        ("a(bb|cc|a?)+a", "abb.cc.a?||+.a."),
    ],
)
def test_re2post(re, post):
    assert post == re2post(re)


def test_post2nfa():
    # TODO: nfa のテストを考える
    x = post2nfa("a")
    assert x.is_out()
    assert x.char == "a"
    y = x.out
    assert y.is_match()


@pytest.mark.parametrize(
    ("re", "s", "is_match"),
    [
        ("a", "a", True),
        ("a", "ab", False),
        ("ab", "ab", True),
        ("ab", "abb", False),
        ("a*", "", True),
        ("a*", "a", True),
        ("a*", "aaaaaa", True),
        ("a*", "aaaaaab", False),
        ("a+", "a", True),
        ("a+", "aaaaaa", True),
        ("a+", "", False),
        ("a+", "aaaaaab", False),
        ("a?", "", True),
        ("a?", "a", True),
        ("a?", "ab", False),
        ("a?", "aaaaaa", False),
        ("a|bb", "a", True),
        ("a|bb", "bb", True),
        ("a|bb", "b", False),
        ("a(b|c)", "ab", True),
        ("a(b|c)", "ac", True),
        ("a(b|c)", "a", False),
        ("a(b|c)", "aa", False),
        ("a(bb)+a", "abba", True),
        ("a(bb)+a", "abbbba", True),
        ("a(bb)+a", "aa", False),
        ("a(bb)+a", "abbba", False),
        ("a(bb)+a", "abbac", False),
    ],
)
def test_match(re, s, is_match):
    if is_match:
        assert match(post2nfa(re2post(re)), s)
    else:
        assert not match(post2nfa(re2post(re)), s)
