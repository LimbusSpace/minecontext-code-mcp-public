# 这是一个故意制造错误的脚本用于测试
import os

# 尝试访问不存在的文件
def read_file():
    with open("/nonexistent/file.txt", "r") as f:
        return f.read()

if __name__ == "__main__":
    print("开始执行...")
    content = read_file()
    print(content)
    print("执行完成")
