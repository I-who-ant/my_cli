# My CLI - Makefile
# 简化的构建和测试命令

.PHONY: help
help:  ## 显示帮助信息
	@echo "My CLI - 可用命令："
	@echo ""
	@echo "【方案1：复用现有虚拟环境】"
	@echo "  make install         使用 pip 安装（开发模式）"
	@echo "  make uninstall       卸载 my_cli 命令"
	@echo ""
	@echo "【方案2：使用 uv 创建独立环境（推荐）】"
	@echo "  make prepare         使用 uv 创建 .venv/ 并安装"
	@echo "  make activate        显示激活虚拟环境的命令"
	@echo "  make clean-venv      删除 .venv/ 虚拟环境"
	@echo ""
	@echo "【其他命令】"
	@echo "  make test            测试 my_cli 命令"
	@echo "  make clean           清理缓存文件"
	@echo "  make format          格式化代码（需要 black）"
	@echo ""

# ============================================================
# 方案1：使用 pip（复用现有虚拟环境）
# ============================================================

.PHONY: install
install:  ## 使用 pip 安装（开发模式）
	pip install -e .
	@echo "✅ my_cli 已安装到当前虚拟环境！"
	@echo "运行：my_cli --help"

.PHONY: uninstall
uninstall:  ## 卸载 my_cli 命令
	pip uninstall -y my-cli
	@echo "✅ my_cli 已卸载"

# ============================================================
# 方案2：使用 uv（创建独立虚拟环境）- 推荐！
# ============================================================

.PHONY: prepare
prepare:  ## 使用 uv 创建 .venv/ 并安装（推荐）
	@echo "检查 uv 是否已安装..."
	@command -v uv >/dev/null 2>&1 || { echo "❌ uv 未安装，正在安装..."; pip install uv; }
	@echo "使用 uv 创建虚拟环境并安装依赖..."
	uv sync
	@echo ""
	@echo "✅ 虚拟环境创建完成！"
	@echo ""
	@echo "下一步："
	@echo "  1. 激活虚拟环境："
	@echo "     source .venv/bin/activate"
	@echo ""
	@echo "  2. 运行命令："
	@echo "     my_cli --help"
	@echo ""
	@echo "或者运行：make activate 查看激活命令"

.PHONY: activate
activate:  ## 显示激活虚拟环境的命令
	@echo "激活虚拟环境："
	@echo "  source .venv/bin/activate"
	@echo ""
	@echo "激活后可以运行："
	@echo "  my_cli --help"
	@echo "  my_cli -c \"Hello World\""

.PHONY: clean-venv
clean-venv:  ## 删除 .venv/ 虚拟环境
	@echo "删除虚拟环境..."
	rm -rf .venv
	@echo "✅ .venv/ 已删除"

# ============================================================
# 通用命令
# ============================================================

.PHONY: test
test:  ## 测试 my_cli 命令
	@echo "测试 my_cli 命令..."
	@my_cli --version
	@my_cli --help
	@my_cli -c "Hello World"
	@echo "✅ 测试通过！"

.PHONY: clean
clean:  ## 清理缓存文件
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ 缓存文件已清理"

.PHONY: format
format:  ## 格式化代码
	@echo "格式化代码..."
	@black my_cli/ 2>/dev/null || echo "提示：需要安装 black（pip install black）"
	@echo "✅ 代码格式化完成"

.PHONY: push
push:  ## 提交并推送代码
	git add .
	git status
	@echo ""
	@echo "请手动提交："
	@echo "  git commit -m '你的提交信息'"
	@echo "  git push origin main"
