# CI 失败分析报告

## 基本信息
- PR: #2706 — 【自动升级】fbthrift容器镜像升级至2026.06.22.00版本.
- 失败类型: build-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: getdeps归档提取失败
- 新模式症状关键词: don't know how to extract, fetcher.py, getdeps, libaio, tar.gz, ArchiveFetcher

## 根因分析

### 直接错误
```
#11 331.3 Traceback (most recent call last):
#11 331.3     raise Exception("don't know how to extract %s" % self.file_name)
#11 331.3 Exception: don't know how to extract /tmp/fbcode_builder_getdeps-ZbuildZbuildZfbcode_builder-root/downloads/libaio-libaio-libaio-0.3.113.tar.gz
```

后续上下文：
```
#11 331.7 Assessing libaio...
#11 ERROR: process "/bin/sh -c ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `build/fbcode_builder/getdeps/fetcher.py:ArchiveFetcher` 的 `_extract_archive` 或等效方法（行号未知，需查看上游代码）
- 失败原因: getdeps 的 `ArchiveFetcher` 在评估提取 libaio 预置归档时，无法识别归档类型（文件扩展名 `.tar.gz` 未被正确匹配），抛出异常导致构建终止。

关键上下文：
- 依赖 `boost`、`fmt`、`gflags`、`glog`、`googletest` 等均构建成功
- 失败发生在 `Assessing libaio...` 阶段，即 getdeps 开始处理 libaio 依赖时
- `fix_getdeps.py` 仅对 `fetcher.py` 中 `_verify_hash` 方法做正则替换（跳过哈希校验），未涉及归档提取逻辑

### 与 PR 变更的关联
此 PR 是全新提交的 fbthrift v2026.06.22.00 Dockerfile。`fix_getdeps.py` 正则 `r'def _verify_hash\(self\):.*?(?=\n    def )'` 在 `fetcher.py` 中可能存在的问题：

1. **正则不匹配**（可能性较高）：fbthrift v2026.06.22.00 的 `fetcher.py` 中 `_verify_hash` 方法签名/缩进/位置已变更，正则匹配失败，`re.sub` 返回原字符串（未生效），导致原始哈希校验逻辑继续执行，进而在某个代码路径中触发归档类型识别错误。
2. **正则匹配过宽**（可能性中等）：正则匹配成功但替换范围超出预期，意外移除了与归档提取相关的代码（如归档类型设置逻辑），导致后续 `_extract_archive` 找不到已知的归档类型。
3. **libaio 归档文件本身异常**（可能性较低）：`libaio-libaio-0.3.113.tar.gz` 二进制文件可能不是有效的 gzip 压缩包，但错误信息 "don't know how to extract" 而非 "failed to extract" 指向归档类型识别阶段，而非实际解压阶段。

## 修复方向

### 方向 1（置信度: 中）
`fix_getdeps.py` 中针对 `_verify_hash` 的正则可能与 fbthrift v2026.06.22.00 的实际 `fetcher.py` 不匹配。需从上游仓库拉取该版本的 `fetcher.py`，确认 `_verify_hash` 方法的实际签名和位置，调整正则表达式使其能正确匹配并替换。同时需检查替换后的文件语法是否完整（`pass` 缩进是否正确、是否破坏了后续方法定义）。

### 方向 2（置信度: 低）
`fetcher.py` 的归档类型检测逻辑本身在 fbthrift v2026.06.22.00 中发生了变更，预置 libaio 归档的文件名 `libaio-libaio-libaio-0.3.113.tar.gz` 不再被其归档类型识别逻辑接受。可能需要额外 patch `fetcher.py` 中负责归档类型检测的方法（如 `_get_archive_type` 或 `_extract_archive`），或者调整 Dockerfile 中 libaio 归档的复制目标文件名以匹配期望的命名模式。

## 需要进一步确认的点
1. 需要获取 fbthrift v2026.06.22.00 上游仓库中 `build/fbcode_builder/getdeps/fetcher.py` 的实际内容，确认：
   - `_verify_hash` 方法的精确签名字符串（是否仍是 `def _verify_hash(self):`）
   - `_verify_hash` 方法体内容（是否仅包含哈希校验，还是也包含归档类型设置逻辑）
   - 归档提取逻辑的入口方法及其归档类型检测机制（是如何根据文件名/URL 判断归档类型的）
2. 需要确认预置的 `libaio-libaio-0.3.113.tar.gz` 是否为有效的 gzip tar 归档文件
3. 需要确认 getdeps manifest 中 libaio 的预期下载 URL/文件名格式，验证 `libaio-libaio-libaio-0.3.113.tar.gz` 文件名是否符合其命名规范

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
code-fixer 在提交前，必须从 fbthrift v2026.06.22.00 的 `build/fbcode_builder/getdeps/fetcher.py` 获取 `_verify_hash` 方法的实际签名和完整方法体，验证新正则确实能匹配目标内容，并确认替换后的文件语法正确（Python 可解析）。同时验证归档提取方法（`_extract_archive` 或等效方法）的归档类型检测逻辑与新正则在 `_verify_hash` 中的替换不会产生冲突。
