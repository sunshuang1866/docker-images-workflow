# 修复摘要

## 修复的问题
`fix_getdeps.py` 中对 `_verify_hash` 方法的正则 patch 在目标方法是类中最后一个方法时静默失败，导致 libaio 哈希校验未被跳过，getdeps 从 pagure.io 重新下载并获取到 HTML 认证页面而非二进制包。

## 修改的文件
- `Others/fbthrift/2026.06.15.00/24.03-lts-sp3/fix_getdeps.py`: 在正则 lookahead 中添加 `|\Z` 备选，使 `_verify_hash` 位于类/文件末尾时也能正确匹配并替换。

## 修复逻辑
原正则 `r'def _verify_hash\(self\):.*?(?=\n    def )'` 依赖 `_verify_hash` 方法之后存在另一个同缩进级别（4 空格）的 `def` 作为匹配终止边界。当 `_verify_hash` 是类中最后一个方法时，该 lookahead 无法满足，`re.sub` 静默返回原内容，`_verify_hash` 未被 patch。getdeps 校验预拷贝的 libaio tarball 哈希失败后从 pagure.io 下载，而 pagure.io 返回 HTML 认证页面导致构建失败。

修复在 lookahead 中增加 `|\Z`（匹配字符串末尾），确保当 `_verify_hash` 后没有同级别的 `def` 时仍能匹配到文件尾部并完成替换。

## 潜在风险
无。`\Z` 仅作为原 lookahead 无法匹配时的 fallback，当后续存在同级别 `def` 时行为与原正则完全一致。不会引入额外的匹配副作用。