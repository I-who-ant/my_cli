"""
My CLI - 安装配置文件

这个文件让你可以把 My CLI 安装成一个可执行命令！

Magic 发生了什么？
1. 运行 `pip install -e .`
2. setuptools 读取 entry_points
3. 在虚拟环境的 bin/ 目录创建 `my_cli` 可执行文件
4. 该文件会调用 `my_cli.cli:my_cli` 函数
5. 现在你可以直接运行 `my_cli -c "Hello"` 了！
"""

from pathlib import Path
from setuptools import setup, find_packages

# 读取 README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# 读取版本号
version_file = Path(__file__).parent / "my_cli" / "__init__.py"
version = "0.1.0"
if version_file.exists():
    for line in version_file.read_text(encoding="utf-8").splitlines():
        if line.startswith("__version__"):
            version = line.split("=")[1].strip().strip('"').strip("'")
            break

setup(
    # 基本信息
    name="my-cli",
    version=version,
    description="从零开始构建你自己的 AI Agent CLI 工具",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/I-who-ant/my_cli",

    # 包配置
    packages=find_packages(),
    python_requires=">=3.10",

    # 依赖
    install_requires=[
        "click>=8.1.0",
    ],

    # 可选依赖（后续阶段需要）
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
        ],
        "stage4": [
            "aiofiles>=23.0.0",
        ],
        "stage5": [
            "pydantic>=2.0.0",
            "openai>=1.0.0",
        ],
        "stage6": [
            "rich>=13.0.0",
            "prompt-toolkit>=3.0.0",
        ],
    },

    # 🎯 这是关键！定义命令行入口
    entry_points={
        "console_scripts": [
            # 格式：命令名=模块.文件:函数名
            "my_cli=my_cli.cli:my_cli",
        ],
    },

    # 分类信息
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
