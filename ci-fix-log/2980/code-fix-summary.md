# 修复摘要

## 修复的问题
无需代码修改。CI 失败为 infra-error：openEuler 仓库镜像 HTTP/2 传输临时中断导致 `dnf install` 无法下载 RPM 包。

## 修改的文件
无（infra-error，无需代码变更）

## 修复逻辑
CI 构建在 `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6` 的 `dnf install` 步骤中，从 openEuler 24.03-LTS-SP4 仓库镜像下载 `gcc-c++` 等 RPM 包时，HTTP/2 传输层多次出现 `Curl error (92): INTERNAL_ERROR` 流错误。重试耗尽所有镜像后下载失败。同类错误同时发生在 `cmake-data` 和 `git-core` 包上（`git-core` 重试后成功），表明是仓库镜像在构建时段的临时性网络问题，与 PR 代码变更完全无关。

PR 仅新增了一个格式正确的 Dockerfile 及三个配置文件的条目，无代码逻辑错误。解决方案为在非高峰时段重新触发 CI 构建（rerun）。

## 潜在风险
无