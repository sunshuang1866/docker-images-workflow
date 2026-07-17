# 修复摘要

## 修复的问题
无需代码修复。CI 失败为基础设施错误（infra-error），由 `repo.openeuler.org` RPM 仓库在 aarch64 架构上的 HTTP/2 流传输不稳定（Curl error 92: INTERNAL_ERROR）导致，与 PR 代码变更无关。

## 修改的文件
无代码修改。

## 修复逻辑
CI 分析报告确认此失败为 infra-error：构建节点 `ecs-build-docker-aarch64-04-sp` 在通过 `dnf install` 从 `repo.openeuler.org` 下载 RPM 包（git-core、gcc-c++、guile）时遭遇 HTTP/2 流错误，所有镜像源重试后仍无法完成下载。Dockerfile 内容本身正确无误，PR 仅新增了标准的基础编译工具安装 + vvenc 构建流程。

建议在 CI 中重新触发一次构建（retry），大概率可以成功。

## 潜在风险
无