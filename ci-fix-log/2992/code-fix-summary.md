# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施错误（infra-error），非 PR 代码问题。

## 修改的文件
无

## 修复逻辑
CI 分析报告明确指出：失败发生在 `dnf install` 阶段，原因是 openEuler 24.03-LTS-SP4 RPM 镜像仓库的 HTTP/2 协议层反复出现 `Curl error (92): Stream error in the HTTP/2 framing layer: INTERNAL_ERROR`，导致 gcc、gcc-gfortran、guile 等多个包下载失败。这是远程仓库服务端的临时性 HTTP/2 传输层故障，与本次 PR 的 Dockerfile 语法和包名无关。PR 中新增的 Dockerfile 及配套元数据均正确无误。

**修复方向**：重试 CI 构建即可。若多次重试仍持续失败，需联系 openEuler 基础设施团队排查 RPM 仓库服务器的 HTTP/2 配置或负载均衡问题。

## 潜在风险
无