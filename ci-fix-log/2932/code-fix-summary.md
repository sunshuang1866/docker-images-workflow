# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施故障（infra-error），BuildKit 容器启动时 Docker daemon 无法定位容器根目录 `/`，导致构建在 Dockerfile 执行前即中止。

## 修改的文件
无

## 修复逻辑
CI 分析报告明确指出：
- 失败发生在 `[internal] booting buildkit` 阶段，Dockerfile 中的任何指令（FROM、RUN 等）均尚未被执行
- 错误 `Could not find the file / in container` 是 Docker daemon / BuildKit 基础设施层面的问题
- 与 PR #2932 的代码变更（新增 glibc 镜像 Dockerfile 及注册条目）无关
- 镜像规范预检阶段已通过

根据任务指令："如果分析报告指出是 infra-error（CI 基础设施问题），在 output_file 中说明无需代码修改，不要强行改代码"，因此不修改任何源文件。

**建议操作**：在 CI 节点上执行 `docker buildx prune -f` 清理残留 BuildKit 容器后重新触发构建；如仍失败，检查 CI 节点的 Docker daemon 健康状态和磁盘空间。

## 潜在风险
无