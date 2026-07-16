# 修复摘要

## 修复的问题
CI 失败由 openEuler 官方 RPM 仓库镜像服务器的 HTTP/2 协议层网络瞬时故障引起（`Curl error (92): Stream error in the HTTP/2 framing layer`），与 PR 代码变更无关。

## 修改的文件
无需修改任何文件。

## 修复逻辑
本次 CI 失败属于 **infra-error**（基础设施错误），非代码问题。PR #2992 新增的 Dockerfile 中 `dnf install` 命令语法正确、包列表完整、依赖关系无误。失败原因是构建时段 `repo.****.org` 的 HTTP/2 服务不稳定，多个 RPM 包下载时遭遇 `Stream error in the HTTP/2 framing layer: INTERNAL_ERROR (err 2)`，其中 `gcc` 包（34 MB）在多次重试后耗尽所有镜像导致最终失败。两个并行构建阶段（builder 和 stage-1）均出现同类错误，进一步确认为服务端问题。

建议操作：等待仓库镜像恢复后重新触发 CI 构建（retry）。

## 潜在风险
无