# My CLI - Makefile
# 简化的构建和测试命令

.PHONY: help
help:  ## 显示帮助信息
	@echo "My CLI - 可用命令："
	@echo ""
	@echo "  make install    安装 my_cli 命令（开发模式）"
	@echo "  make uninstall  卸载 my_cli 命令"
	@echo "  make test       测试 my_cli 命令"
	@echo "  make clean      清理缓存文件"
	@echo "  make format     格式化代码（需要 black）"
	@echo "  make push       提交并推送代码"
	@echo ""

.PHONY: install
install:  ## 安装 my_cli 命令（开发模式）
	pip install -e .
	@echo "✅ my_cli 安装完成！"
	@echo "运行：my_cli --help"

.PHONY: uninstall
uninstall:  ## 卸载 my_cli 命令
	pip uninstall -y my-cli
	@echo "✅ my_cli 已卸载"

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
