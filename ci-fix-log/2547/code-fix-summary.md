# 修复摘要

## 修复的问题
`fix_getdeps.py` 中 `_verify_hash` 的替换正则无法匹配最后方法（无后续 `def` 作为锚点），导致哈希校验绕过失效，getdeps 重新从 pagure.io 下载 libaio 时获取到 HTML 页面而非 tar.gz 归档，构建失败。

## 修改的文件
- `Others/fbthrift/2026.06.08.00/24.03-lts-sp3/fix_getdeps.py`: 修复 `_verify_hash` 方法体的正则表达式，增加对"最后方法"和"文件末尾"的锚点支持，并将替换体从 `pass` 改为 `return True`。

## 修复逻辑
原正则 `r'def _verify_hash\(self\):.*?(?=\n    def )'` 的 lookahead 仅匹配下一个同缩进级别的 `def` 定义。当 `_verify_hash` 是所在类的最后一个方法时，后续不存在同缩进的 `def`，导致 `re.sub` 匹配失败、返回原始字符串，哈希绕过未生效。getdeps 对预置的 libaio tarball 执行原始哈希校验，校验失败后触发远程下载，pagure.io 返回 HTML 页面导致构建退出码 1。

新正则 `r'def _verify_hash\(self\):.*?(?=\n    def |\n[a-zA-Z@]|\Z)'` 增加了两个替代锚点：
- `\n[a-zA-Z@]` — 匹配类结束后的下一个顶层定义（下一 class、顶层函数、装饰器），覆盖最后方法场景
- `\Z` — 匹配文件结尾，作为最终兜底

同时将替换体从 `pass` 改为 `return True`，避免调用方对返回值进行 falsy 判断时误认为校验失败。

## 潜在风险
- 如果 fbcode_builder 的 `fetcher.py` 中方法体使用不同缩进风格（如 2 空格缩进、tab 缩进），`\n    def ` 仍可能无法匹配。但基于现有代码中 `gflags`/`glog`/`googletest` 均下载成功的事实，`fetcher.py` 中其他方法的正则正常工作，表明缩进风格一致，风险低。
- `return True` 替代 `pass` 不会改变语义（原方法体在成功时隐式返回 `None`，但调用方未必检查返回值），风险极低。