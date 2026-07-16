# 修复摘要

## 修复的问题
infra-error：无需代码修改。CI 构建失败由 `repo.openeuler.org` 镜像仓库 HTTP/2 服务端间歇性故障导致，与 PR 代码变更无关。

## 修改的文件
无。

## 修复逻辑
分析报告确认为 `infra-error`（置信度：高）。失败发生在 `dnf install` 从 `repo.openeuler.org` 下载 RPM 包时遭遇 HTTP/2 流错误（Curl error 92: INTERNAL_ERROR），属于 openEuler 镜像仓库服务端的临时性网络/协议层故障。PR 新增的 Dockerfile 中 `dnf install` 命令语法正确，基础镜像拉取成功，代码本身无问题。按照指令，infra-error 场景下不强行修改代码，直接重新触发 CI 构建即可。

## 潜在风险
无。