# 修复摘要

## 修复的问题
无需代码修改 — 此为 CI 基础设施问题 (infra-error)。

## 修改的文件
无

## 修复逻辑
CI 失败原因为 openEuler 24.03-LTS-SP4 软件仓库与 CI 构建环境之间的 HTTP/2 网络传输层不稳定，多个 RPM 包（`cmake-data`、`git-core`、`gcc-c++`）下载时遭遇 `Curl error (92): Stream error in the HTTP/2 framing layer`，最终 `gcc-c++` 在所有镜像源重试后失败导致 `dnf install` 退出。

PR 新增的 `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile` 语法正确，`dnf install` 所列包名均存在于目标仓库中（依赖解析阶段已成功列出 258 个包），失败纯属网络传输层问题，与 PR 代码无关。

**处理方式**：在 CI 中重新触发构建，或等待仓库网络状况稳定后重试。

## 潜在风险
无