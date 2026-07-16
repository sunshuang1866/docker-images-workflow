# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施问题（infra-error）：openEuler 24.03-LTS-SP4 仓库镜像服务器在构建时段 HTTP/2 协议层不稳定，导致 `gcc-c++` 等 RPM 包下载出现 `Curl error (92): Stream error in the HTTP/2 framing layer`。

## 修改的文件
无。PR 新增的 Dockerfile 语法和包名均正确，失败与代码变更无关。

## 修复逻辑
分析报告明确指出：此失败是 CI 基础设施/网络临时性问题，不是代码缺陷。`dnf install` 命令本身正确，`cmake-data` 和 `git-core` 在重试后成功下载，仅 `gcc-c++`（约 13MB）因多次 HTTP/2 流错误耗尽重试次数而失败。应重新触发 CI 构建，等待镜像服务恢复后即可通过。

若多次重新触发后仍然失败，需排查 openEuler 仓库侧问题（方向 2）。

## 潜在风险
无