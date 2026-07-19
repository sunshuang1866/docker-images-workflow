# 修复摘要

## 修复的问题
无需代码修改。CI 失败为 infra-error：openEuler 24.03-LTS-SP4 官方软件仓库镜像发生 HTTP/2 协议层错误（Curl error 92: INTERNAL_ERROR），导致 `dnf install` 下载 RPM 包失败。

## 修改的文件
无（基础设施问题，非代码缺陷）

## 修复逻辑
分析报告明确指出：失败根因是 openEuler 24.03-LTS-SP4 仓库镜像在响应 HTTP/2 请求时发生流级协议错误（`Stream error in the HTTP/2 framing layer`），多个 RPM 包（`gcc-gfortran`、`glibc-devel`、`guile`、`gcc`）下载均受此影响，最终 `gcc` 包因所有镜像均尝试失败而报 `No more mirrors to try`。该错误与 PR 变更的 Dockerfile 内容无关，属于上游仓库的临时性基础设施故障。

建议：等待上游仓库恢复后重新触发 CI 构建。若问题持续，可考虑在 Dockerfile 中为 `dnf install` 添加重试参数（如 `--setopt=retries=10`）或切换备用镜像源，但这超出了当前 infra-error 的修复范围。

## 潜在风险
无。不涉及任何代码修改。