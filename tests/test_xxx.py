"""一个不存在的测试模块"""
import pytest


def test_failing():
    """一个故意失败的测试"""
    # 引用不存在的变量
    assert nonexistent_variable == 10


def test_syntax_error():
    """有语法错误的测试"""
    x = \
    y = 2
    assert x + y == 5
