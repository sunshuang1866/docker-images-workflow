# 修复摘要

## 修复的问题
无需代码修改。CI 失败为 BuildKit 基础设施层面的偶发性故障（构建器容器启动后根文件系统不可访问），与 PR 代码变更完全无关。

## 修改的文件
无

## 修复逻辑
CI 分析报告判定失败类型为 `infra-error`。错误 `Error response from daemon: Could not find the file / in container` 发生在 BuildKit bootstrap 阶段（`[internal] booting buildkit`），早于任何 Dockerfile 指令的解析与执行。PR 仅新增了 `Others/glibc/2.42/24.03-lts-sp4/Dockerfile` 及配套元数据更新，均为纯配置文件/文档变更，不可能影响 Docker daemon 或 BuildKit 运行时的容器启动行为。按照修复规则，`infra-error` 类型无需修改代码，重试 CI 构建即可。

## 潜在风险
无