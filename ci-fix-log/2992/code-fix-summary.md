# 修复摘要

## 修复的问题
无需代码修改。CI 失败原因为 openEuler 24.03-LTS-SP4 RPM 软件仓库镜像在 HTTP/2 协议层面持续返回 `INTERNAL_ERROR`（Curl error 92），属于基础设施问题（infra-error），与 PR 代码变更无因果关系。

## 修改的文件
无

## 修复逻辑
本次 CI 失败是基础设施问题，非代码问题。Builder 阶段的 `dnf install` 命令语法正确、包名正确（对比 stage-1 已成功解析依赖并开始下载部分包可确认），失败纯粹由上游仓库 HTTP/2 服务端错误导致。gcc、gcc-gfortran、guile 等多个 RPM 包下载均报 `Curl error (92): HTTP/2 stream INTERNAL_ERROR`，最终 gcc 在所有镜像上均失败。

**建议操作**：重试 CI 构建。该问题可能是 SP4 仓库镜像的临时性 HTTP/2 服务端故障，一段时间后可能自行恢复。若持续失败，可能需要联系 openEuler 仓库运维排查 SP4 镜像的 HTTP/2 协议层问题。

## 潜在风险
无 — 本次未修改任何文件。