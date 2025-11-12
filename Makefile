# My CLI - Makefile
# 便捷命令集合

.DEFAULT_GOAL := help

.PHONY: help
help:  ## 显示帮助信息
	@echo "My CLI - 可用命令："
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
	@echo ""

.PHONY: prepare
prepare:  ## 安装依赖（自动检测环境）
	@echo "检查 uv 是否已安装..."
	@command -v uv >/dev/null 2>&1 || { \
		echo "❌ uv 未安装"; \
		echo ""; \
		echo "安装方法："; \
		echo "  pip install uv"; \
		echo ""; \
		exit 1; \
	}
	@if [ -n "$$CONDA_DEFAULT_ENV" ]; then \
		echo "检测到 conda 环境: $$CONDA_DEFAULT_ENV"; \
		echo "在当前环境中安装依赖..."; \
		uv pip install -e .; \
		echo ""; \
		echo "✅ 依赖已安装到 conda 环境: $$CONDA_DEFAULT_ENV"; \
		echo ""; \
		echo "运行测试："; \
		echo "  my_cli --help"; \
	else \
		echo "未检测到 conda 环境，创建 .venv/ 虚拟环境..."; \
		uv sync; \
		echo ""; \
		echo "✅ 虚拟环境创建完成！"; \
		echo ""; \
		echo "下一步："; \
		echo "  1. 激活虚拟环境："; \
		echo "     source .venv/bin/activate"; \
		echo ""; \
		echo "  2. 运行命令："; \
		echo "     my_cli --help"; \
	fi

.PHONY: activate
activate:  ## 显示激活虚拟环境的命令
	@echo "激活虚拟环境："
	@echo "  source .venv/bin/activate"
	@echo ""
	@echo "激活后可以运行："
	@echo "  my_cli --version"
	@echo "  my_cli -c \"Hello World\""

.PHONY: test
test:  ## 测试 my_cli 命令
	@echo "测试 my_cli 命令..."
	@command -v my_cli >/dev/null 2>&1 || { \
		echo "❌ my_cli 未找到"; \
		echo ""; \
		echo "请先运行："; \
		echo "  make prepare"; \
		echo "  source .venv/bin/activate"; \
		exit 1; \
	}
	@echo "1. 测试版本..."
	@my_cli --version
	@echo ""
	@echo "2. 测试帮助..."
	@my_cli --help | head -n 5
	@echo ""
	@echo "3. 测试基本命令..."
	@my_cli -c "Hello World" | head -n 10
	@echo ""
	@echo "✅ 测试通过！"

.PHONY: clean
clean:  ## 清理缓存文件
	@echo "清理 Python 缓存..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ 缓存已清理"

.PHONY: clean-venv
clean-venv:  ## 删除虚拟环境
	@echo "删除虚拟环境 .venv/..."
	rm -rf .venv
	@echo "✅ 虚拟环境已删除"
	@echo ""
	@echo "重新创建请运行："
	@echo "  make prepare"

.PHONY: dev
dev:  ## 安装开发依赖
	uv sync --extra dev
	@echo "✅ 开发依赖已安装"

.PHONY: stage4
stage4:  ## 安装阶段 4 依赖
	uv sync --extra stage4
	@echo "✅ 阶段 4 依赖已安装"

.PHONY: stage5
stage5:  ## 安装阶段 5 依赖
	uv sync --extra stage5
	@echo "✅ 阶段 5 依赖已安装"

.PHONY: stage6
stage6:  ## 安装阶段 6 依赖
	uv sync --extra stage6
	@echo "✅ 阶段 6 依赖已安装"

.PHONY: all
all:  ## 安装所有依赖
	uv sync --extra all
	@echo "✅ 所有依赖已安装"
