# CI 失败分析报告

## 基本信息
- PR: #2607 — 【自动升级】fbthrift容器镜像升级至2026.06.15.00版本.
- 失败类型: build-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: getdeps libaio校验失败
- 新模式症状关键词: Assessing libaio, _verify_hash, fetcher.py, getdeps, fbthrift, exit code: 1

## 根因分析

### 直接错误
```
#11 332.9 Building googletest...
#11 332.9 Assessing libaio...
#11 ERROR: process "/bin/sh -c git clone -b ${VERSION} --depth 1 https://github.com/facebook/fbthrift.git /build && ..." did not complete successfully: exit code: 1
------
Dockerfile:18
```

日志在 `Assessing libaio...` 之后被截断，未显示 libaio 评估阶段的具体错误信息。

### 根因定位
- 失败位置: Dockerfile:18 (RUN 指令中 getdeps.py 构建 fbthrift 阶段)
- 失败原因: fbcode_builder 的 getdeps.py 在评估/下载 libaio 依赖时失败（exit code 1），日志截断导致精确错误信息缺失

### 与 PR 变更的关联

PR 新增了 `fix_getdeps.py` 脚本，其中通过正则替换跳过 libaio 的哈希校验：

```python
re.sub(
    r'def _verify_hash\(self\):.*?(?=\n    def )',
    'def _verify_hash(self):\n        pass',
    c2,
    flags=re.DOTALL
)
```

该正则依赖 `_verify_hash` 方法之后存在另一个 `def` 作为边界标记（lookahead `(?=\n    def )`）。若 `_verify_hash` 是 `fetcher.py` 中所在类的最后一个方法，则正则无法匹配，哈希校验代码未被替换，导致 getdeps 在校验本地提供的 `libaio-libaio-0.3.113.tar.gz` 时与上游 manifest 中记录的哈希值不匹配而失败。

此外，日志在 `Assessing libaio...` 处截断，存在其他可能：如 libaio 下载源不可达、tar.gz 内部目录结构与 getdeps 期望不符等。

## 修复方向

### 方向 1（置信度: 中）
验证并修复 `fix_getdeps.py` 中 `_verify_hash` 的替换逻辑，确保无论该方法在类中的位置如何（包括作为最后一个方法的情况），都能正确替换。例如将正则的结束边界从 `(?=\n    def )` 改为匹配到类结束或下一个顶层定义，或使用更稳健的匹配策略（匹配到方法末尾的 `return` 或空行后的非缩进行）。

### 方向 2（置信度: 低）
如果哈希校验替换已正确生效，则问题可能在 libaio 下载阶段。需确认 getdeps 在 `--allow-system-packages` 模式下对已提供的本地 tar.gz 文件的处理流程是否正确（manifest 中的 URL 是否可达、本地文件复制路径是否匹配 getdeps 期望的文件名）。

## 需要进一步确认的点
- 日志在 `Assessing libaio...` 后截断，需获取该位置之后的完整日志（libaio 评估/下载/校验阶段的完整输出）以精确定位错误类型
- 需确认 `fetcher.py` 中 `_verify_hash` 方法是否是所在类的最后一个方法，以验证方向 1 的正则失效假设
- 需确认 libaio 的 getdeps manifest（在 fbthrift 仓库的 `build/fbcode_builder/manifests/libaio`）中记录的哈希值，以及本地提供的 tar.gz 是否与之匹配

---

## 第二轮分析（事后复盘，人工确认）

第一轮 code-fix 提交的正则仍然失败，经人工排查确认真实根因：

### 实际根因
fbthrift v2026.06.15.00 的 `build/fbcode_builder/getdeps/fetcher.py` 中，`_verify_hash` 方法签名为：

```python
def _verify_hash(self) -> None:
```

带有 `-> None` 返回类型注解。第一轮诊断假设"该方法是类中最后一个方法导致 lookahead 失效"，该假设错误——`_verify_hash` 后面还有 `_download_dir` 方法，lookahead 本可以匹配；真正失败原因是正则开头 `def _verify_hash\(self\):` 无法匹配带注解的签名 `def _verify_hash(self) -> None:`，导致 `re.sub` 静默未替换。

### 日志截断是诊断误判的根源
CI 日志被截断于 `Assessing libaio...`，未能看到后续 `_verify_hash` 抛出的 hash mismatch 异常，导致分析只能基于 PR diff 推断，推断方向合理但结论错误。

### 正确修复
将正则改为 `def _verify_hash\([^)]*\).*?:` 加 `re.DOTALL`，可匹配任意返回类型注解：

```python
re.sub(
    r'def _verify_hash\([^)]*\).*?:.*?(?=\n(?: {4,}|\t)(?:def |@)|\n\S|\Z)',
    'def _verify_hash(self):\n        pass',
    c2,
    flags=re.DOTALL
)
```

已从上游 v2026.06.15.00 获取 fetcher.py 实际内容验证正则匹配，修复 PR #2614 CI 通过。
