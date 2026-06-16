# 修复摘要

## 修复的问题
`fix_getdeps.py` 中跳过 libaio 哈希校验的正则表达式无法匹配 `_verify_hash` 是该类最后一个方法的情况，导致 hash 校验未被跳过，构建在 "Assessing libaio..." 阶段失败。

## 修改的文件
- `Others/fbthrift/2026.06.15.00/24.03-lts-sp3/fix_getdeps.py`: 将正则替换的结束边界从仅 `(?=\n    def )` 扩展为 `(?=\n    def |\nclass |\Z)`，覆盖方法为类/文件末尾方法的场景。

## 修复逻辑
CI 分析报告指出 `getdeps.py` 在 "Assessing libaio..." 时以 exit code 1 失败。原始正则 `def _verify_hash\(self\):.*?(?=\n    def )` 依赖下一个 `def ` 方法定义作为匹配终点。当 `_verify_hash` 是类中最后一个方法时（fbthrift v2026.06.15.00 可能调整了方法顺序），无法找到后续的 `def` 边界，正则匹配失败，`_verify_hash` 方法保持原样，哈希校验照常执行，预置的 libaio tarball 因哈希不匹配导致构建中断。

修复方案：在正则边界中增加 `\nclass ` 和 `\Z` 两个替代终点，分别覆盖后续为类定义结尾和文件结尾的场景，确保 `_verify_hash` 方法在任何位置都能被成功替换为 no-op。

## 潜在风险
- 如果 `_verify_hash` 和下一个类级方法之间存在 `@decorator` 装饰器，正则会吞掉该装饰器（这是原始正则也存在的问题，非本次引入）。
- 如果 fbthrift 上游完全移除或重命名了 `_verify_hash` 方法，正则将静默不匹配，构建仍会失败（需要进一步的日志验证）。