# CI 失败分析报告

## 基本信息
- PR: #2804 — 【自动升级】fbthrift容器镜像升级至2026.06.29.00版本.
- 失败类型: build-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 正则 raw 字符串转义错误
- 新模式症状关键词: don't know how to extract, _verify_hash, re.sub, raw string, \n, fetcher.py, libaio

## 根因分析

### 直接错误
```
#11 336.4 Assessing libaio...
#11 336.4 Traceback (most recent call last):
#11 336.4     raise Exception("don't know how to extract %s" % self.file_name)
#11 336.4 Exception: don't know how to extract /tmp/fbcode_builder_getdeps-ZbuildZbuildZfbcode_builder-root/downloads/libaio-libaio-libaio-0.3.113.tar.gz
```

### 根因定位
- 失败位置: `Others/fbthrift/2026.06.29.00/24.03-lts-sp3/fix_getdeps.py`:16-21（re.sub 正则部分）
- 失败原因: `fix_getdeps.py` 中用于跳过 libaio 哈希校验的 `re.sub` 正则表达式使用了 Python 原始字符串（`r'...'`），其中的 `\n` 在原始字符串中被解释为两个字面字符（反斜杠 + n），而非换行符。这导致正则无法匹配 `fetcher.py` 中实际的 `_verify_hash` 方法定义，补丁**静默失败**。`_verify_hash` 未被替换为 pass-through，原始的 SHA256 校验逻辑仍在运行——校验预置的自定义 tarball 时哈希值不匹配，getdeps 在校验失败后的异常流程中尝试提取无效/被删除的文件，触发 `don't know how to extract` 异常。

### 与 PR 变更的关联
PR 新增的 `fix_getdeps.py` 中的正则表达式存在转义错误，直接导致三步补丁中最关键的一步（跳过哈希校验）静默失败。这是 **PR 自身变更引入的缺陷**。此外，Dockerfile 中 COPY 的 tarball 目标文件名 `libaio-libaio-libaio-0.3.113.tar.gz`（多出冗余的 `libaio-` 前缀）与上游 manifest 中从 URL 推导的文件名 `libaio-libaio-0.3.113.tar.gz` **可能不一致**，构成次要风险点。

## 修复方向

### 方向 1（置信度: 高）—— 修复正则表达式的 \n 转义
- **问题**: `fix_getdeps.py` 第 16–21 行的 `re.sub` 调用的正则模式中使用了原始字符串 `r'...\n    def ...'`，其中的 `\n` 是两个字面字符而非换行符，正则永远无法匹配。
- **修复思路**: 将 `r'def _verify_hash\(self[^)]*\)[^:]*:.*?(?=\n    def )'` 改为使用实际换行符或 `\s` 通配符的正则。例如使用非原始字符串 `'\n'` 或 `r'(?s)def _verify_hash\(self[^)]*\)[^:]*:.*?(?=\n    def )'`（其中 `\n` 由字符串转义产生），确保正则能匹配源码中的真实换行边界。

### 方向 2（置信度: 中）—— 修正 tarball 文件名
- **问题**: Dockerfile 第 21 行将 tarball 目标命名为 `libaio-libaio-libaio-0.3.113.tar.gz`，而上游 libaio manifest 中从 URL 推导的文件名通常为 `libaio-libaio-0.3.113.tar.gz`（少一个 `libaio-` 前缀）。即便正则修复后哈希校验被跳过，getdeps 仍可能因文件名不匹配而无法找到预置文件。
- **修复思路**: 将 Dockerfile 中的目标文件名从 `libaio-libaio-libaio-0.3.113.tar.gz` 修正为 `libaio-libaio-0.3.113.tar.gz`，或在 `fix_getdeps.py` 中同步修改 manifest 中的 URL 字段以对齐文件名。

## 需要进一步确认的点
1. **上游 fetcher.py 中 `_verify_hash` 的实际签名**：需从 fbthrift v2026.06.29.00 的 `build/fbcode_builder/getdeps/fetcher.py` 获取 `_verify_hash` 方法的真实定义，确认新正则是否能精确匹配（包括参数列表、类型注解、返回值注解等）。
2. **上游 libaio manifest 中的 URL 文件名**：从 `build/fbcode_builder/manifests/libaio` 确认 `url` 字段末尾的文件名是什么，验证 Dockerfile 中的目标文件名是否需要同步修改。
3. **Git LFS 或二进制文件完整性**：日志无法完全排除预置的 `libaio-libaio-0.3.113.tar.gz` 本身为 Git LFS 指针文件或残缺文件的可能。若方向 1 修复后仍报 "don't know how to extract"，则需检查该二进制文件的实际内容。

## 修复验证要求
- **code-fixer 必须从 fbthrift v2026.06.29.00 的 `build/fbcode_builder/getdeps/fetcher.py` 获取 `_verify_hash` 方法的实际签名**（包括参数列表和返回类型注解），验证补正后的正则表达式确实能匹配该方法的定义体，且不会误匹配到其他方法。
- **code-fixer 必须从 `build/fbcode_builder/manifests/libaio` 获取 `url` 字段**，验证目标文件名与上游期望一致后再提交。
