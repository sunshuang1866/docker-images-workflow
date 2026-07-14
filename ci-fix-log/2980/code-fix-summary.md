# 修复摘要

## 修复的问题
无需代码修改。CI 失败属于基础设施问题（infra-error）：openEuler 24.03-LTS-SP4 官方仓库镜像在 HTTP/2 传输层发生流错误，导致 `gcc-c++` 等 RPM 包下载失败。

## 修改的文件
无（无需修改任何代码文件）

## 修复逻辑
CI 分析报告指出：
- 失败直接原因是 `Curl error (92): Stream error in the HTTP/2 framing layer`，`gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm` 在所有镜像重试后仍下载失败
- Dockerfile 中的 `dnf install` 命令本身正确无误，DNF 成功解析了全部 258 个依赖包
- 该失败与 PR #2980 的代码改动无关，属于 CI 构建环境与 `repo.*.org` 镜像站之间的网络基础设施问题

**建议操作**：重新触发 CI 构建。HTTP/2 流错误通常是临时的服务端或 CDN 问题，重新运行 CI 大概率可以直接通过。

## 潜在风险
无