# 修复摘要

## 修复的问题
无需代码修改。CI 失败为 infra-error（上游 openEuler 24.03-LTS-SP4 aarch64 软件仓库 `repo.openeuler.org` 在构建时段出现 HTTP/2 流错误），与 PR 代码无关。

## 修改的文件
无

## 修复逻辑
CI 分析报告明确指出该失败类型为 `infra-error`。PR #2991 仅新增了 `vvenc` 镜像的 Dockerfile 及相关元数据文件，Dockerfile 中的 `dnf install` 命令内容正确。失败根因是 `repo.openeuler.org` 的 aarch64 节点在构建时段对多个 RPM 包（`git-core`、`gcc-c++`、`guile`）的 HTTP/2 下载响应出现 `INTERNAL_ERROR`（curl error 92），属于上游仓库侧的网络波动问题。

建议操作：**重试 CI**（re-run failed job）。若重试多次仍失败，可在 Dockerfile 中为 dnf 配置 `--setopt=retries=10` 增加重试次数或禁用 HTTP/2 回退到 HTTP/1.1。

## 潜在风险
无