# 修复摘要

## 修复的问题
无需代码修复。CI 失败为 infra-error（基础设施问题），由 `repo.openeuler.org` 镜像站在 aarch64 架构上的 HTTP/2 服务端瞬时故障（Curl error 92: INTERNAL_ERROR）导致 dnf 下载 RPM 包失败，与 PR 代码变更无关。

## 修改的文件
无

## 修复逻辑
CI 分析报告确认该失败属于 infra-error，Dockerfile 语法和内容均无问题。失败原因是在 aarch64 构建节点上执行 `dnf install` 时，openEuler 镜像站的 HTTP/2 服务端多次返回流错误，导致 git-core、gcc-c++、guile 等 RPM 包下载失败。此为镜像站服务端瞬时故障，重试 CI 构建即可，无需对代码做任何修改。

## 潜在风险
无