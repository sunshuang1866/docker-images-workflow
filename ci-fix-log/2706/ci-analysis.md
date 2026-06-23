# CI 失败分析报告

## 基本信息
- PR: #2706 — 【自动升级】fbthrift容器镜像升级至2026.06.22.00版本.
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 正则patch未匹配
- 新模式症状关键词: expected sha256, but got, _verify_hash, re.sub, fetcher.py, fix_getdeps.py

## 根因分析

### 直接错误

```
#11 379.1 Traceback (most recent call last):
#11 379.1     raise Exception(
#11 379.1 Exception: https://pagure.io/libaio/archive/libaio-0.3.113/libaio-libaio-0.3.113.tar.gz: expected sha256 716c7059703247344eb066b54ecbc3ca2134f0103307192e6c2b7dab5f9528ab but got b93da241a72971350fffba828e19acd925a3b18f6b0534fab5d326d46779403b
#11 379.4 Assessing libaio...
#11 379.4 Download with https://pagure.io/libaio/archive/libaio-0.3.113/libaio-libaio-0.3.113.tar.gz -> /tmp/fbcode_builder_getdeps-ZbuildZbuildZfbcode_builder-root/downloads/libaio-libaio-libaio-0.3.113.tar.gz ...
#11 ERROR: process "/bin/sh -c git clone ... && python3 /tmp/fix_getdeps.py && ./build/fbcode_builder/getdeps.py ... build fbthrift" did not complete successfully: exit code: 1
```

### 根因定位

- 失败位置: `Others/fbthrift/2026.06.22.00/24.03-lts-sp3/fix_getdeps.py`:14-20
- 失败原因: `fix_getdeps.py` 中的正则 `r'def _verify_hash\(self\):.*?(?=\n    def )'` 未能匹配 fbthrift v2026.06.22.00 版本中 `build/fbcode_builder/getdeps/fetcher.py` 的 `_verify_hash` 方法，导致哈希校验未被跳过，本地预置的 libaio 压缩包因 SHA256 不匹配而构建失败。

### 与 PR 变更的关联

PR 此次新增了 fbthrift v2026.06.22.00 的 Dockerfile 和配套的 `fix_getdeps.py` 脚本。`fix_getdeps.py` 的设计意图是通过正则替换将 `fetcher.py` 中 `_verify_hash` 方法的实现体替换为 `pass`（跳过哈希校验），从而让预置的本地 libaio tarball 通过校验。但该正则表达式与目标文件中实际的方法签名/结构不匹配，`re.sub` 未命中时返回原始内容原样写回，哈希校验未被绕过，构建失败。

**正则可能未命中的原因**（按可能性排序）：
1. `_verify_hash` 方法签名中包含参数（如 `_verify_hash(self, url, path)`），正则要求精确匹配 `(self):`
2. `_verify_hash` 方法是类中最后一个方法，其后不存在 `\n    def ` 满足 lookahead 条件
3. 上游代码使用了类型标注（如 `def _verify_hash(self) -> None:`），冒号前有额外内容
4. `re.sub` 确实命中但替换后的文件因 Python 语法错误导致运行时走了其他分支

## 修复方向

### 方向 1（置信度: 高）

Dockerfile 中不再依赖正则去 patch `fetcher.py` 的 `_verify_hash` 方法，而是改用更可靠的方式预置 libaio 压缩包：在 Dockerfile 的 `cp` 命令之后，直接在 `fetcher.py` 中删除或注释掉哈希校验逻辑，方式可以是：
- 在 `cp` 和 `python3 fix_getdeps.py` 之间用 `sed` 直接注释掉 `fetcher.py` 中调用哈希校验的函数或条件分支
- 或者修改 `fix_getdeps.py` 中的正则，使其能同时匹配有参和无参的 `_verify_hash` 方法签名（如 `r'def _verify_hash\(self[^)]*\):'`），并放宽末尾 lookahead 条件

### 方向 2（置信度: 中）

如果 `re.sub` 确实生效但替换后代码有语法问题，则应检查替换结果 `def _verify_hash(self):\n        pass` 的缩进是否与原方法对齐（原方法缩进可能不是 4 空格），使用捕获组保留原始缩进再拼接 `pass` 语句。

## 需要进一步确认的点

1. 需要获取 fbthrift v2026.06.22.00 源代码中 `build/fbcode_builder/getdeps/fetcher.py` 文件的实际内容，确认 `_verify_hash` 方法的精确签名（参数列表、类型标注、装饰器）以及该方法在类中的位置（是否是最后一个方法）
2. 确认 pagure.io 上 libaio-0.3.113 的下载 URL 是否仍然有效（日志中响应 Content-Type 为 `text/html`，可能已失效或需要认证）
3. 确认预置的 `libaio-libaio-0.3.113.tar.gz` 的 SHA256 是否为 `b93da241a72971350fffba828e19acd925a3b18f6b0534fab5d326d46779403b`

## 修复验证要求

code-fixer 在提交前，必须从 fbthrift v2026.06.22.00 仓库获取 `build/fbcode_builder/getdeps/fetcher.py` 的实际内容，确认 `_verify_hash` 方法的当前签名和位置，验证新的 patch 方式（正则或 sed）确实能匹配目标代码并禁掉哈希校验。修复后应在 Docker 环境中验证 `getdeps.py` 构建 fbthrift 时不再因 libaio 哈希校验而失败。
