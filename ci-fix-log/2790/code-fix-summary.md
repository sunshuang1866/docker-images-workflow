# 修复摘要

## 修复的问题
CI appstore 规范预检对根级 README.md 报 [Path Error]，根因是 eulerpublisher CI 工具的 `format.py` 中 `_check_all_file_paths` 函数对根级文件的路径处理存在缺陷（空 prefix 导致生成绝对路径 `/README.md` 而非相对路径 `README.md`），同时 PR 原始变更中存在 `24.03-lts-sp3` 标签重复条目。

## 修改的文件
- `README.md`: 移除重复的 `- [24.03-lts-sp3](https://repo.openeuler.org/openEuler-24.03-LTS-SP3/docker_img/)` 条目（该标签已作为第一条 `24.03-lts-sp3, 24.03, latest` 出现，重复列出属于内容冗余）

## 修复逻辑

1. **内容修复（已完成）**：PR 原始变更中 `24.03-lts-sp3` 同时出现在两条条目中（一次作为 `latest` 组合标签，一次作为独立条目），构成重复。已移除独立的重复条目，保留 `- [24.03-lts-sp3, 24.03, latest]...` 作为唯一引用。

2. **CI 基础设施问题（无法在本仓库修复）**：通过分析 `eulerpublisher/update/container/app/format.py` 源码，确认 [Path Error] 的触发逻辑如下：
   - `parse_image_prefix("README.md")` 因文件无目录层级（`len(contents) == 1`）返回空 prefix `""`
   - `_check_all_file_paths` 调用 `"{0}/README.md".format("")` 生成路径 `/README.md`
   - `os.path.exists("/README.md")` 检测的是文件系统根目录 `/README.md`，而非工作目录下的 `README.md`，导致路径检查失败
   - 此为 CI 工具（eulerpublisher 仓库）的 bug，与 PR #2512 的 `.claude/README.md` 路径校验失败属于同一类问题

   该 CI 工具的修复应在 `eulerpublisher` 仓库的 `format.py` 中进行，例如在 `_check_all_file_paths` 中对空 prefix 做特殊处理，或使用 `os.path.join` 代替字符串格式化。本仓库（docker-images-workflow）无法修复此问题。

## 潜在风险
无。移除的重复条目 `24.03-lts-sp3` 仍以 `- [24.03-lts-sp3, 24.03, latest]` 形式作为首条保留，不影响信息完整性和用户可发现性。