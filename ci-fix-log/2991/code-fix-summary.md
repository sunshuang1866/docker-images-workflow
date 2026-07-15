# 修复摘要

## 修复的问题
无需代码修改。该 CI 失败为 `infra-error`——openEuler 官方镜像仓库 `repo.openeuler.org` 在 aarch64 构建节点上出现 HTTP/2 协议层面的间歇性流重置（Curl error 92），导致 `guile` 等多个 RPM 包下载中断，与 PR 的 Dockerfile 代码变更无关。

## 修改的文件
无

## 修复逻辑
CI 分析报告明确判定失败类型为 `infra-error`（置信度: 高），根因为 openEuler 镜像站 HTTP/2 服务瞬时不稳定。Dockerfile 中 `dnf install -y git gcc gcc-c++ make cmake` 命令语法正确，构建逻辑与同项目已有的 vvenc 24.03-lts-sp3 Dockerfile 结构一致，无需代码层面的修改。

## 建议操作
重新触发 CI 构建。多次重试中 git-core 和 gcc-c++ 均已下载成功，说明镜像站可访问，只是间歇性故障。若多次重试仍失败，可考虑在 Dockerfile 的 dnf install 命令中添加 `--setopt=retries=10` 参数增加重试次数。

## 潜在风险
无