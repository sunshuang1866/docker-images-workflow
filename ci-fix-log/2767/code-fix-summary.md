# 修复摘要

## 修复的问题
rsyslog 8.2606.0 构建失败：`./configure` 找不到 `libyaml` 开发文件（`libyaml support is enabled by default but yaml-0.1 was not found`），同时缺少 `cmp`/`diff` 命令（`diffutils` 未安装）。

## 修改的文件
- `Others/rsyslog/8.2606.0/24.03-lts-sp3/Dockerfile`: 在 `dnf install` 行补充 `libyaml-devel` 和 `diffutils` 两个包。

## 修复逻辑
rsyslog 8.2606.0 默认启用 libyaml 支持，`./configure` 在未检测到 libyaml 开发文件时直接报错退出。Dockerfile 原有的 `dnf install` 命令遗漏了 `libyaml-devel` 包（新版 rsyslog 新增依赖），同时也缺少 `diffutils` 基础工具包（导致 `cmp`/`diff` 命令缺失的警告）。补充这两个包即可解决构建失败。

## 潜在风险
无。`libyaml-devel` 和 `diffutils` 均为 openEuler 24.03-LTS-SP3 标准仓库中的包，不会与已有依赖冲突。