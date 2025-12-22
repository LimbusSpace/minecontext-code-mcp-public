# 测试文件 - 故意失败的 pytest 用例

import pytest
import os


def test_file_not_exists():
    """测试一个预期会失败的用例"""
    with open('nonexistent_file_12345.txt', 'r') as f:
        content = f.read()
        assert content == "hello"


def test_divide_by_zero():
    """另一个会失败的用例"""
    result = 10 / 0
    assert result == 5


def test_import_error():
    """导入不存在的模块"""
    import nonexistent_module_xyz
    assert True


def test_wrong_assertion():
    """简单的断言失败"""
    x = 1 + 1
    assert x == 3, f"期望 3 但实际是 {x}"


def test_value_error():
    """数值错误"""
    raise ValueError("这是一个故意引发的 ValueError")


if __name__ == "__main__":
    pytest.main([__file__])
