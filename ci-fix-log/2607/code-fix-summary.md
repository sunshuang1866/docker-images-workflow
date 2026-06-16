# 修复摘要

## 修复的问题
`fix_getdeps.py` 中的正则表达式未能正确替换 `_verify_hash` 方法，导致预置的本地 `libaio` 文件被哈希校验失败删除后，从已失效的上游 URL 重新下载 HTML 页面而构建失败。

## 修改的文件
- `Others/fbthrift/2026.06.15.00/24.03-lts-sp3/fix_getdeps.py`: 修复两处问题：(1) `_verify_hash` 正则替换的签名匹配和贪婪匹配缺陷；(2) 新增 `_download` 方法文件存在时的跳过逻辑。

## 修复逻辑
1. **根因**: 原正则 `def _verify_hash\(self\):.*?(?=\n    def )` 存在两个 bug：
   - 签名部分 `def _verify_hash\(self\):` 不匹配实际的 `def _verify_hash(self) -> None:`（含返回类型标注），导致替换静默失败
   - `.*` 配合 `re.DOTALL` 从 `(self)` 后贪婪匹配跨行直到文件末尾的最后一个 `:`，会吞噬 `_download_dir`、`_download` 等多个后续方法
   **修复**: 将签名部分改为 `[^\n]*` 限定仅匹配当前行，方法体用 `.*?` + lookahead 精确匹配到下一个方法定义。
2. **防御性加固**: 在新版 `_download` 方法开头增加文件存在检查（`if os.path.exists(self.file_name): return`），确保即使有其他代码路径触发下载，也不会覆盖已预置的本地文件。

## 潜在风险
- 如果 `libaio-libaio-0.3.113.tar.gz` 本地文件本身损坏或不兼容（非有效 tar.gz），则提取阶段会失败，但此类失败属于文件质量问题而非本修复引入。
- `_download` 的跳过逻辑是针对 `_download` 方法签名和缩进格式，若 fbthrift 上游大幅重构 fetcher.py 的该部分代码，string replace 可能失效，但由于 `_verify_hash` 已可靠跳过，`_download` 仅作为双重保险，不影响核心功能。