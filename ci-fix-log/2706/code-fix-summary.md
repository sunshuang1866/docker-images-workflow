# 修复摘要

## 修复的问题
`fix_getdeps.py` 中的正则表达式未能匹配 fbthrift v2026.06.22.00 版本中 `fetcher.py` 的 `_verify_hash` 方法签名（包含 `-> None` 返回类型标注），导致哈希校验未被跳过，libaio 压缩包因 SHA256 不匹配而构建失败。

## 修改的文件
- `Others/fbthrift/2026.06.22.00/24.03-lts-sp3/fix_getdeps.py`: 将第 17 行的正则从 `r'def _verify_hash\(self\):.*?(?=\n    def )'` 改为 `r'def _verify_hash\(self[^)]*\)[^:]*:.*?(?=\n    def )'`，使其能匹配带返回类型标注（如 `-> None`）和/或额外参数的方法签名。

## 修复逻辑
分析报告指出 `_verify_hash` 方法签名可能包含参数或返回类型标注，而原正则精确匹配 `(self):` 无法命中实际签名 `def _verify_hash(self) -> None:`。

已从上游 `v2026.06.22.00` 获取 `build/fbcode_builder/getdeps/fetcher.py` 验证：实际方法签名为 `def _verify_hash(self) -> None:`。使用 Python `re.sub` 对实际源文件内容进行测试，原正则**未命中**（返回原文原封不动），新正则 `r'def _verify_hash\(self[^)]*\)[^:]*:.*?(?=\n    def )'` **成功匹配**并替换为 `def _verify_hash(self):\n        pass`。

新正则中的 `[^)]*` 匹配括号内可能的额外参数，`[^:]*` 匹配 ` -> None` 等返回类型标注，提高了对上游未来变更的兼容性。

## 潜在风险
- 如果上游 `_verify_hash` 方法包含带冒号的复杂返回类型标注（如 `-> dict[str, int]`），`[^:]*` 会在此处失败。但当前和预期合理的 Python 类型标注中冒号不会出现在返回值之前，风险极低。
- 如果 `_verify_hash` 之后不存在任何 `def`（即它是类中最后一个方法），`(?=\n    def )` 前瞻条件无法匹配。当前上游代码中 `_verify_hash` 后还有多个方法，暂不存在此问题。