# 修复摘要

## 修复的问题
无需代码修改。CI 失败为 `repo.openeuler.org` 仓库源 HTTP/2 传输层临时故障（Curl error 92），属于基础设施问题，与 PR 代码无关。

## 修改的文件
无（infra-error，不涉及代码修改）

## 修复逻辑
CI 在 aarch64 runner 上执行 `dnf install` 时，`repo.openeuler.org` 返回 HTTP/2 流错误（`Stream error in the HTTP/2 framing layer: INTERNAL_ERROR`），导致 git-core、gcc-c++、guile 等多个 RPM 包下载失败，最终 guile 耗尽所有镜像源后安装失败。此错误发生在远端仓库服务器侧，与 Dockerfile 中 `RUN dnf install -y git gcc gcc-c++ make cmake` 命令正确性无关。所有 PR 变更文件（Dockerfile、README.md、image-info.yml、meta.yml）内容均正确无误，无需任何代码修改。建议重新触发 CI 构建（retry），待 openEuler 仓库源 HTTP/2 服务恢复后构建应能通过。

## 潜在风险
无