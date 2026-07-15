# 修复摘要

## 修复的问题
无需代码修复。CI 失败原因为 openEuler 镜像站 `repo.openeuler.org` 的 HTTP/2 服务端临时性故障，属于 `infra-error`（CI 基础设施问题），与 PR #2991 的代码变更无关。

## 修改的文件
无

## 修复逻辑
CI 构建在 `Dockerfile:6` 执行 `dnf install` 下载 RPM 包时，`repo.openeuler.org` 的 aarch64 仓库返回了多个 `Curl error (92): Stream error in the HTTP/2 framing layer`，导致 `guile` 等依赖包下载失败。这是镜像站服务端 HTTP/2 流未正常关闭的间歇性问题，与 PR 新增的 vvenc Dockerfile 及配套文件无关。

建议操作：重新触发 CI 构建（retry），大概率可正常通过。若多次重试仍失败，可联系 openEuler 基础设施团队排查镜像站 aarch64 仓库的 HTTP/2 服务可用性。

## 潜在风险
无