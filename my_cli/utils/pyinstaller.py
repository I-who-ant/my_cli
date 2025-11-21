"""
PyInstaller 打包配置 ⭐ Stage 30

用于 PyInstaller 打包时收集必要的数据文件和子模块。

对应源码：kimi-cli-fork/src/kimi_cli/utils/pyinstaller.py
"""

from __future__ import annotations

try:
    from PyInstaller.utils.hooks import collect_data_files, collect_submodules

    hiddenimports = collect_submodules("my_cli.tools")
    datas = (
        collect_data_files(
            "my_cli",
            includes=[
                "agents/**/*.yaml",
                "agents/**/*.md",
                "deps/bin/**",
                "prompts/**/*.md",
                "tools/**/*.md",
                "CHANGELOG.md",
            ],
        )
        + collect_data_files(
            "dateparser",
            includes=["**/*.pkl"],
        )
        + collect_data_files(
            "fastmcp",
            includes=["../fastmcp-*.dist-info/*"],
        )
    )
except ImportError:
    # PyInstaller not installed
    hiddenimports = []
    datas = []


__all__ = ["hiddenimports", "datas"]
