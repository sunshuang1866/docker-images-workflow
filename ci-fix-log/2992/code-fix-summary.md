# 修复摘要

## 修复的问题
无需代码修改 — 该失败为 CI 基础设施问题（infra-error），openEuler 24.03-LTS-SP4 官方软件仓库的 HTTP/2 服务端不稳定，导致 RPM 包下载失败，与 PR 代码无关。

## 修改的文件
无

## 修复逻辑
CI 失败分析报告明确指出：
- 失败类型为 `infra-error`，置信度：高
- 根本原因是 openEuler 24.03-LTS-SP4 仓库（`repo.****.org`）的 HTTP/2 服务端在传输大型 RPM 包时频繁出现 `HTTP/2 stream INTERNAL_ERROR`，curl 重试所有可用镜像后仍失败
- 与 PR 变更无关：Dockerfile 中 `dnf install` 包列表、`sed` 编译配置改编、`make noGUI` 构建命令均语法正确
- 所有下载错误均为 `[MIRROR]` 级别的网络传输错误，多个独立镜像源均返回相同错误

属于外部仓库基础设施不稳定问题，不应通过修改 PR 代码来规避。

## 潜在风险
无。建议等待 openEuler 24.03-LTS-SP4 仓库服务恢复后重新触发 CI 构建。如果该错误持续出现，建议向 openEuler 基础设施团队报告仓库 HTTP/2 服务端稳定性问题。