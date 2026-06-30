# 修复摘要

## 修复的问题
fix_getdeps.py 缺少 v2026.06.22.00 版本中已有的第三项补丁（libaio manifest subdir 修正），补全该补丁以与上游 v2026.06.29.00 的 fetcher.py 和 manifest 兼容。

## 修改的文件
- `Others/fbthrift/2026.06.29.00/24.03-lts-sp3/fix_getdeps.py`: 添加缺失的 libaio manifest subdir 修复补丁（第 23-27 行），将 `subdir = libaio-libaio-0.3.113` 替换为 `subdir = libaio-0.3.113`

## 修复逻辑
1. CI 分析报告指向两项可能原因：(a) fbthrift 源码与 folly 的 API 不兼容导致 ninja 编译失败，(b) fix_getdeps.py 中 `_verify_hash` 正则不匹配。
2. 已从 fbthrift v2026.06.29.00 上游 `build/fbcode_builder/getdeps/fetcher.py` 获取实际文件并通过 Python 验证：当前正则 `r'def _verify_hash\(self[^)]*\)[^:]*:.*?(?=\n    def )'` 匹配成功，方向 (b) 已排除。
3. 对比 v2026.06.22.00 的工作版本，发现 v2026.06.29.00 的 fix_getdeps.py 缺少 libaio manifest subdir 补丁。该补丁将 manifest 中 `subdir = libaio-libaio-0.3.113` 修正为 `subdir = libaio-0.3.113`，以匹配预置 tarball 内部真实目录结构。
4. CI 构建虽进展至 876/895，但缺少该补丁可能导致 libaio 安装在错误路径，影响后续 fbthrift 编译的链接阶段。
5. 若上游 manifest 中 subdir 已正确（即替换为无操作），该补丁不会产生副作用。

## 潜在风险
- CI 分析置信度为"低"，实际编译错误（未能从截断日志中获取）可能是 fbthrift 与 folly 的 API 不兼容。若此修复后构建仍失败，需降级 fbthrift 版本或通过 getdeps 指定兼容的 folly commit hash。
- libaio manifest subdir 修复仅在 `subdir = libaio-libaio-0.3.113` 精确匹配时才生效；若上游 manifest 格式变更，该补丁将无操作，不会引入新问题。