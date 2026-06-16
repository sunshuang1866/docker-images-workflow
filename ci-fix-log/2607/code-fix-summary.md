# 修复摘要

## 修复的问题
`fix_getdeps.py` 的 `_verify_hash` 正则表达式无法匹配 fbthrift v2026.06.15.00 中带类型注解（`-> None`）的方法签名，导致哈希校验未被跳过，预置的 libaio tar.gz 被删除后从 pagure.io 下载了 HTML 错误页面。

## 修改的文件
- `Others/fbthrift/2026.06.15.00/24.03-lts-sp3/fix_getdeps.py`: 修复了 `_verify_hash` 正则表达式以兼容类型注解，并新增 `_download` 方法补丁以在预置文件存在时跳过网络下载。

## 修复逻辑
1. **`_verify_hash` 正则修复**：原正则 `r'def _verify_hash\(self\):.*?'` 要求 `(self)` 后紧跟 `:`，但 fbthrift v2026.06.15.00 的 fetcher.py 中该方法是 `def _verify_hash(self) -> None:`。正则不匹配导致 `re.sub` 不执行任何替换，`_verify_hash` 未被修补，正常执行哈希校验，发现预置 tar.gz 的 SHA256 与预期不符后删除文件。修复后的正则 `r'def _verify_hash\(self\).*?:.*?'` 使用 `.*?:` 兼容方法签名中的类型注解。

2. **`_download` 跳过下载**：在 `_download` 方法中 `self._download_dir()` 之后插入文件存在性检查——若 `self.file_name` 已存在且大小 > 0 字节则立即返回，不发起 HTTP 下载。这作为双保险，即使未来版本中哈希校验补丁失效，也能防止预置文件被网络下载覆盖。

## 潜在风险
- `_download` 补丁使用精确字符串匹配 `def _download(self) -> None:\n        self._download_dir()`，若 fbthrift 未来版本改变该方法格式（如添加装饰器、改变缩进），补丁可能不生效。但 libaio 预置文件复制在 Dockerfile 中发生在补丁之前，此补丁为双保险措施，即使失效也不会导致功能退化。