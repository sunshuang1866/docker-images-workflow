# 修复摘要

## 修复的问题
CI 失败由 eulerpublisher 工具的 `_check_all_file_paths` 函数 bug 导致，非 README.md 内容问题。README.md 内容无需修改（上一轮修复已移除重复的 `24.03-lts-sp3` 条目）。

## 修改的文件
无（README.md 当前内容正确，无需进一步修改）

## 修复逻辑

### 根本原因分析（CI 工具 bug）

通过获取 eulerpublisher 源码 (`update/container/app/format.py`) 分析确认，`check_report` 函数对 `change_files` 中的每个文件执行路径校验：

1. 对于根目录下的 `README.md`，`parse_image_prefix` 函数因 `len(contents) == 1` 返回 `("", "")`（空前缀）
2. `_check_all_file_paths` 使用 `DOC_FILES_PATH_FORMAT["README"] = "{0}/README.md"` 拼接路径
3. 空前缀拼接后得到 `correct_path = "/README.md"`（**绝对路径**）
4. `os.path.exists("/README.md")` 在 CI 工作目录中恒为 `False`，导致报告 `[Path Error] The expected path should be /README.md`

本地验证：
```
correct_path = '/README.md'
os.path.exists('/README.md') = False   # 绝对路径不存在
os.path.exists('README.md') = True     # 相对路径存在
```

### README.md 内容状态
- 重复的 `24.03-lts-sp3` 已在 commit `eb68566a9` 中移除
- 所有新标签（`24.03-lts-sp3` 组合标签、`25.09`、`24.03-lts-sp2` 独立标签）的 URL 均经验证可达
- 内容格式与既有条目一致

### 结论
此 CI 失败应归类为 **infra-error**（CI 基础设施/工具问题）。修复需在 eulerpublisher 仓库的 `format.py` 中处理根目录文件的路径拼接逻辑，非本仓库 README.md 可解决。

## 潜在风险
无。当前未对 README.md 做任何代码修改，不引入风险。