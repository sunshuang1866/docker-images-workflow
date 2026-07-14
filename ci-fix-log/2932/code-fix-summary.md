# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施故障（BuildKit 容器启动失败），与 PR 代码变更无关。

## 修改的文件
无

## 修复逻辑
CI 分析报告明确指出失败类型为 `infra-error`，错误发生在 Docker BuildKit 初始化阶段（`[internal] booting buildkit`），早于任何 Dockerfile 指令的执行。错误信息 `Error response from daemon: Could not find the file / in container` 表明 Docker 守护进程在 CI Runner（`ecs-build-docker-x86-hk`）上创建 BuildKit builder 容器后文件系统挂载异常。PR 仅新增了标准的 glibc 源码构建 Dockerfile 及更新了 README、image-info.yml、meta.yml，与构建基础设施故障无因果关系。

建议操作：清理 CI Runner 上残留的 buildx builder 实例并重试 CI job，或由基础设施团队排查 Runner 的 Docker 守护进程状态。

## 潜在风险
无