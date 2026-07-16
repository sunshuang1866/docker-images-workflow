# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施瞬时故障（infra-error），与 PR 代码无关。

## 修改的文件
无

## 修复逻辑
CI 失败根因是 `repo.openeuler.org` 镜像站在 aarch64 架构上出现 HTTP/2 流错误（Curl error 92），导致多个 RPM 包下载失败。这是镜像站服务端瞬时故障，属于 CI 基础设施问题。PR 变更仅为新增 vvenc 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及配套元数据，Dockerfile 中的 `dnf install` 命令语法完全正确。修复方式：重新触发 CI 构建即可。

## 潜在风险
无