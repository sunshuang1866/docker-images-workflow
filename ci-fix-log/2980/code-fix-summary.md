# 修复摘要

## 修复的问题
无需代码修改。CI 失败属于基础设施错误（infra-error），与 PR 代码变更无关。

## 修改的文件
无（未修改任何文件）

## 修复逻辑
CI 失败的直接原因是 Docker 构建过程中 `dnf install` 从 openEuler 24.03-LTS-SP4 仓库镜像下载 RPM 包时，HTTP/2 协议层反复出现 `INTERNAL_ERROR`（Curl error 92），导致 gcc-c++ 等包下载失败。该错误属于仓库镜像的瞬时网络问题，与 PR #2980 新增的 Dockerfile 及配套文件无关。PR 中的 Dockerfile 语法正确，所列软件包均为 openEuler 仓库合法包名。建议在 CI 中重新触发构建即可。

## 潜在风险
无