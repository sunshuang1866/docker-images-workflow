# CI 失败分析报告

## 基本信息
- PR: #2607 — 【自动升级】fbthrift容器镜像升级至2026.06.15.00版本.
- 失败类型: build-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: Python regex 补丁未命中
- 新模式症状关键词: Assessing libaio, getdeps.py, _verify_hash, fix_getdeps.py, did not complete successfully, exit code: 1

## 根因分析

### 直接错误
```
#11 338.1 Building googletest...
#11 338.1 Assessing libaio...
#11 ERROR: process "/bin/sh -c git clone -b ${VERSION} --depth 1 https://github.com/facebook/fbthrift.git /build &&     cd /build &&     mkdir -p /tmp/fbcode_builder_getdeps-ZbuildZbuildZfbcode_builder-root/downloads &&     cp /tmp/libaio.tar.gz /tmp/fbcode_builder_getdeps-ZbuildZbuildZfbcode_builder-root/downloads/libaio-libaio-libaio-0.3.113.tar.gz &&     python3 /tmp/fix_getdeps.py &&     ./build/fbcode_builder/getdeps.py --allow-system-packages --install-prefix /usr/local build fbthrift" did not complete successfully: exit code: 1
------
Dockerfile:18
```

### 根因定位
- 失败位置: `Others/fbthrift/2026.06.15.00/24.03-lts-sp3/Dockerfile`:18 (RUN 命令中 `getdeps.py` 执行阶段)
- 失败原因: `getdeps.py` 在 "Assessing libaio..." 阶段失败（exit code 1），最可能的直接原因是 `fix_getdeps.py` 中的正则表达式未能成功匹配 `fetcher.py` 中的 `_verify_hash` 方法，导致哈希校验未被跳过，手动放置的 libaio tarball 哈希校验失败。

### 与 PR 变更的关联
**由 PR 变更触发。** 本次 PR 新增了整个 fbthrift 2026.06.15.00 的 Dockerfile 及配套文件，其中：

1. 新增 `fix_getdeps.py` 脚本，意图通过正则替换将 `fetcher.py` 中的 `_verify_hash` 方法体替换为 `pass`，以跳过 libaio 哈希校验。
2. 该正则表达式为 `r'def _verify_hash\(self\):.*?(?=\n    def )'`，其 lookahead `(?=\n    def )` 要求 `_verify_hash` 方法之后必须还有另一个 `def` 方法定义。若 `_verify_hash` 是类中最后一个方法、或上游代码的缩进/结构与此正则不匹配，则该正则**静默失败**（`re.sub` 无匹配时返回原文），哈希校验未被实际禁用。
3. libaio tarball 是手动 COPY 到容器内的，并非由 getdeps 从上游 URL 下载，因此其哈希值与 manifest 中记录的期望值不匹配，哈希校验必然失败。

## 修复方向

### 方向 1（置信度: 中）
将 `fix_getdeps.py` 中对 `_verify_hash` 的修改从正则替换改为更稳健的方式：直接替换整个 `fetcher.py` 文件中 `def _verify_hash` 方法为仅含 `pass` 的版本，或使用不依赖后续方法存在的正则模式（如匹配到方法体结束的 `return` 语句或空行+dedent）。具体可改为匹配 `def _verify_hash(self):` 到下一个同缩进级别的非空行（即下一个方法或类结束）。

### 方向 2（置信度: 低）
检查 `fetcher.py` 在当前 tag (`v2026.06.15.00`) 中 `_verify_hash` 方法的实际代码结构。若该方法已被移除、重命名或签名变更，则需调整 `fix_getdeps.py` 中的文件路径或匹配逻辑。同时确认 libaio tarball 的目标文件名 `libaio-libaio-libaio-0.3.113.tar.gz` 是否与 getdeps 期望的下载文件名完全一致（需与 getdeps manifest 中 libaio 的 URL hash 命名规则匹配）。

## 需要进一步确认的点
1. **无法获取 `getdeps.py` 在 "Assessing libaio..." 之后的具体错误输出**：日志在 `Assessing libaio...` 之后直接跳到 ERROR，中间无任何 libaio 相关的详细错误信息（如 hash mismatch 提示、file not found 等）。需在本地或 CI 环境中重现该构建，捕获完整的 getdeps 输出以确认精确错误。
2. **`fetcher.py` v2026.06.15.00 的实际代码**：需查看上游 `facebook/fbthrift` 仓库 tag `v2026.06.15.00` 中 `build/fbcode_builder/getdeps/fetcher.py` 的 `_verify_hash` 方法代码，确认其类结构、缩进及是否为类中最后一个方法，以判定正则是否能匹配。
3. **libaio tarball 命名规则**：需确认 `libaio-libaio-libaio-0.3.113.tar.gz` 是否为 getdeps 对该版本 libaio 期望的正确下载文件名（与 manifest 中 URL hash 一致）。
