# CI 失败分析报告

## 基本信息
- PR: #2547 — 【自动升级】fbthrift容器镜像升级至2026.06.08.00版本.
- 失败类型: build-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: libaio哈希校验绕过失败
- 新模式症状关键词: Assessing libaio, exit code: 1, _verify_hash, fix_getdeps, fetcher.py

## 根因分析

### 直接错误
```
#11 334.7 Assessing libaio...
#11 ERROR: process "/bin/sh -c git clone -b ${VERSION} --depth 1 https://github.com/facebook/fbthrift.git /build &&     cd /build &&     mkdir -p /tmp/fbcode_builder_getdeps-ZbuildZbuildZfbcode_builder-root/downloads &&     cp /tmp/libaio.tar.gz /tmp/fbcode_builder_getdeps-ZbuildZbuildZfbcode_builder-root/downloads/libaio-libaio-libaio-0.3.113.tar.gz &&     python3 /tmp/fix_getdeps.py &&     ./build/fbcode_builder/getdeps.py --allow-system-packages --install-prefix /usr/local build fbthrift" did not complete successfully: exit code: 1
------
Dockerfile:18
```

### 根因定位
- 失败位置: `Others/fbthrift/2026.06.08.00/24.03-lts-sp3/Dockerfile`:18 (RUN 命令中的 getdeps.py 调用)
- 失败原因: `fix_getdeps.py` 中绕过 libaio 哈希校验的正则表达式未能匹配 `fetcher.py` 中实际的 `_verify_hash` 方法体，导致哈希校验未被跳过，getdeps 在校验预置的 libaio tarball 时校验失败，构建以 exit code 1 终止

### 与 PR 变更的关联
本次 PR 新增了 `fix_getdeps.py` (`Others/fbthrift/2026.06.08.00/24.03-lts-sp3/fix_getdeps.py:12-20`)，设计用于绕过 libaio 哈希校验。但其中的正则替换存在缺陷：

```python
re.sub(
    r'def _verify_hash\(self\):.*?(?=\n    def )',
    'def _verify_hash(self):\n        pass',
    c2,
    flags=re.DOTALL
)
```

该正则依赖以下假设：
1. `_verify_hash` 之后紧跟的下一个方法定义恰好以 `\n    def ` (换行+4空格+def) 开头——若 `fetcher.py` 实际缩进不是 4 空格（如 8 空格、tab），则不匹配。
2. `_verify_hash` 不是类中的最后一个方法（存在后续 `def` 作为前瞻锚点）——若该方法是末尾方法，则无后续 `def`，正则回退整个文件仍不匹配。
3. 方法签名恰好为 `def _verify_hash(self):`，不含类型注解或参数差异。

以上任一条件不满足，`re.sub` 返回原字符串（无修改），文件被原样写回，哈希校验未被绕过。getdeps 在 `Assessing libaio...` 阶段尝试校验预置的 `libaio-libaio-0.3.113.tar.gz` 的哈希值时失败，导致整个 Docker 构建终止。

日志中仅在 `Assessing libaio...` 后立即报 `exit code: 1`，无具体错误详情（Docker 构建输出截断），但根据 PR 中 `fix_getdeps.py` 的意图（绕过哈希校验）和失败时机（恰好在 libaio 评估阶段），可推断哈希校验失败为直接原因。

## 修复方向

### 方向 1（置信度: 中）
修改 `fix_getdeps.py` 中绕过哈希校验的方式，不使用依赖缩进格式和前瞻锚点的正则，改用更稳健的方法替换 `_verify_hash` 方法体，例如：
- 匹配 `def _verify_hash` 起至下一个同缩进级别的 `def ` 或类定义结束为止的方法体
- 或者使用 `sed` 直接在 RUN 命令中处理，如 `sed -i '/def _verify_hash/,/^    def /{s/^/pass  # /}'` 注释掉方法体

### 方向 2（置信度: 低）
如果方向 1 修复后仍失败，可能存在其他问题：
- libaio 预置 tarball 的文件名不符合 getdeps 的预期命名规则（当前为 `libaio-libaio-libaio-0.3.113.tar.gz`，三层 `libaio` 前缀疑为异常）
- 上游 `https://pagure.io/libaio/libaio.git` 不可达（网络问题）
- getdeps 的 openEuler 发行版适配不完整（除识别外，包名映射等环节也需要额外处理）

## 需要进一步确认的点
1. **缺失的具体错误信息**：日志在 `Assessing libaio...` 后无任何 getdeps 的报错内容（如 hash mismatch、404、连接超时等），需要获取未被截断的完整 Docker 构建日志以确认确切的错误类型。
2. **`fetcher.py` 中 `_verify_hash` 的实际方法体结构**：需查看 `build/fbcode_builder/getdeps/fetcher.py` 中 `_verify_hash` 方法的实际缩进格式、行数和后续方法定义情况，以确认正则替换确实失败。
3. **libaio 的 getdeps manifest 定义**：需确认 libaio 在 fbthrift 构建清单中的下载 URL、预期哈希值和预期 tarball 文件名，以排除文件名不匹配或哈希值已变更的可能性。
