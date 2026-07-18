# 修复摘要

## 修复的问题
本次 CI 失败为 **infra-error**（CI 基础设施问题），无需修改代码。

## 修改的文件
无（infra-error，无需代码修改）

## 修复逻辑
CI 失败的直接原因是 openEuler 24.03-LTS-SP4 的 RPM 仓库镜像服务器 (`repo.****.org`) 在处理 HTTP/2 请求时发生内部错误（`INTERNAL_ERROR (err 2)`），导致 `cmake-data`、`git-core`、`gcc-c++` 三个 RPM 包下载失败，`dnf` 在重试所有镜像后仍无法下载而报错退出。

该错误与 PR #2980 的代码变更完全无关。PR 仅新增了 grads 2.2.3 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及相关元数据文件，`dnf install` 的包列表和语法均正确。

**建议操作**：
- 等待仓库镜像恢复后重新触发 CI 构建
- 如问题持续出现，联系 openEuler 镜像站运维排查 HTTP/2 协议栈配置

## 潜在风险
无（未修改任何代码）