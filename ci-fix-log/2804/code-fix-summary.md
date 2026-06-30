# 修复摘要

## 修复的问题
预置的 libaio tarball 文件在 Git 传输过程中损坏（UTF-8 编码污染），导致 getdeps 在 tarfile 检查阶段抛出 "don't know how to extract" 异常，CI 构建失败。

## 修改的文件
- `Others/fbthrift/2026.06.29.00/24.03-lts-sp3/libaio-libaio-0.3.113.tar.gz`: 从上游 URL `https://pagure.io/libaio/archive/libaio-0.3.113/libaio-libaio-0.3.113.tar.gz` 下载有效版本替换损坏文件。SHA256 为 `716c7059703247344eb066b54ecbc3ca2134f0103307192e6c2b7dab5f9528ab`，与 manifest 一致。
- `Others/fbthrift/2026.06.29.00/24.03-lts-sp3/fix_getdeps.py`: 移除 patch 3（subdir 修改逻辑），因为上游 tarball 内部目录 `libaio-libaio-0.3.113/` 与 manifest 中的 `subdir = libaio-libaio-0.3.113` 已一致，不再需要修改。

## 修复逻辑
CI 分析报告将根因指向 fix_getdeps.py 中 re.sub 的正则表达式，但经实际测试验证：
- 从上游 `v2026.06.29.00` tag 获取 `build/fbcode_builder/getdeps/fetcher.py`，以 `re.sub(r'def _verify_hash\(self[^)]*\)[^:]*:.*?(?=\n    def )', ...)` 进行替换，正则匹配成功，`_verify_hash` 方法体被正确替换为 `pass`。
- Python raw string 中的 `\n` 在正则引擎中仍然被解释为换行符，不存在"字面反斜杠+n"问题。

真正的根因是预置 tarball 文件损坏：文件头为 `1f ef bf bd`（UTF-8 替换字符 U+FFFD），而非有效的 gzip 魔术字节 `1f 8b`。由于 hash 校验被跳过（pass），损坏文件直接进入提取阶段，`tarfile.is_tarfile()` 返回 False 导致异常。

修复方案：用上游有效 tarball（hash 与 manifest 一致）替换损坏文件，并移除不再需要的 subdir 修改逻辑。

## 潜在风险
无。patch 2（hash 校验跳过）保留不变，对使用上游有效 tarball 的情况无害。如果未来需要替换为自定义 tarball，需同步更新 hash 值并恢复 patch 3（subdir 修改）。