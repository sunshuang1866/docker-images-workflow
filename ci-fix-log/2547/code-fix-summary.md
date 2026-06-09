# 修复摘要

## 修复的问题
pagure.io 对 libaio 下载请求返回 HTML 鉴权页面，导致 getdeps 将 HTML 内容覆盖本地预置的 tar.gz 文件，后续解压失败。修复方式为在 `fix_getdeps.py` 中新增 URL 替换逻辑，将 libaio 的下载源从 pagure.io 远程 URL 替换为本地 `file:///tmp/libaio.tar.gz`。

## 修改的文件
- `Others/fbthrift/2026.06.08.00/24.03-lts-sp3/fix_getdeps.py`: 新增步骤 3，遍历 `build/fbcode_builder/` 目录下所有文件，将包含 `pagure.io` 和 `libaio` 的文件中的远程下载 URL 替换为 `file:///tmp/libaio.tar.gz`，使 getdeps 在 "Assessing libaio" 阶段直接使用本地文件，不再发起 HTTP 请求。

## 修复逻辑
CI 分析报告指出，虽然 `fix_getdeps.py` 已通过 `cp` 预置本地 tar.gz 并补丁跳过哈希校验，但 getdeps 仍会从 pagure.io 发起远程下载并用 HTML 鉴权页面覆写本地文件。本次修复在现有两个补丁的基础上新增第三步：在 getdeps 的 manifest/recipe 文件中将 libaio 的下载 URL 替换为 `file:///tmp/libaio.tar.gz`，从源头阻止 getdeps 发起远程 HTTP 下载。这对应于分析报告中置信度最高的"方向 1"修复方案。

## 潜在风险
- 该修复依赖 `file://` URL 方案被当前版本的 fbthrift/getdeps 正确支持。
- 如果 libaio 依赖声明不在 `build/fbcode_builder/` 目录下（如在 fbthrift 仓库的其他位置），URL 替换可能不会被命中，但分析报告确认 libaio 是通过 getdeps 管理的 fbcode_builder 依赖，该位置是标准路径。
- 保留的 `cp` 命令（Dockerfile 第 21 行）与 `file://` URL 指向同一文件，互为冗余保障，无冲突风险。