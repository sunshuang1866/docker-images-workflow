# 修复摘要

## 修复的问题
无需代码修改 — 本次 CI 失败属于 infra-error，由 openEuler 24.03-LTS-SP4 软件仓库镜像 HTTP/2 协议层临时故障导致。

## 修改的文件
无

## 修复逻辑
CI 失败的直接原因是 `dnf install` 过程中 openEuler 24.03-LTS-SP4 仓库镜像（`repo.openeuler.org`）返回 `Curl error (92): Stream error in the HTTP/2 framing layer`，导致多个 RPM 包（gcc、gcc-gfortran、glibc-devel、guile）下载失败。所有镜像均被尝试后仍无法完成下载。

本次 PR 仅新增了一个标准格式的 Dockerfile，其中 `dnf install` 的写法与其他已有版本（如 `24.03-lts-sp3`）完全一致，语法和包名均无错误。失败与 PR 代码变更无关，属于 CI 基础设施的临时性问题。

**建议操作**：等待仓库镜像恢复后重新触发 CI 构建。若多次重试仍持续失败，需确认 `repo.openeuler.org` 上的 24.03-LTS-SP4 仓库状态。

## 潜在风险
无