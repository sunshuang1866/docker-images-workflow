# 修复摘要

## 修复的问题
无代码修复。CI 失败为 `infra-error`，由 `repo.openeuler.org` 仓库服务器端 HTTP/2 流中断导致（`Curl error (92): Stream error in the HTTP/2 framing layer ... INTERNAL_ERROR (err 2)`），与 PR 代码变更无关。

## 修改的文件
无

## 修复逻辑
CI 分析报告明确指出该失败与 PR 无关，属于 CI 基础设施/网络问题（HTTP/2 服务端不稳定）。PR 仅新增 vvenc 1.14.0 在 openEuler 24.03-lts-sp4 上的 Dockerfile 及配套元数据文件，Dockerfile 中 `dnf install` 的命令语法和包名均正确。失败纯粹由 `repo.openeuler.org` 镜像仓库的临时性 HTTP/2 协议层故障引起，重试构建即可。

## 潜在风险
无