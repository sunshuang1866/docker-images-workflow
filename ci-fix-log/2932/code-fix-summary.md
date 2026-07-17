# 修复摘要

## 修复的问题
CI 失败为基础设施问题（infra-error），与 PR 代码变更无关，无需代码修改。

## 修改的文件
无（未修改任何文件）

## 修复逻辑
CI 失败发生在 BuildKit 容器启动阶段（`[internal] booting buildkit`），早于任何 Dockerfile 指令的执行。错误信息 `Could not find the file / in container buildx_buildkit_euler_builder_*` 表明 Docker daemon 在创建 buildkit 容器后无法访问其根文件系统，属于 Docker 存储驱动或构建节点环境层面的临时性/环境性问题。

本 PR 仅新增 `Others/glibc/2.42/24.03-lts-sp4/Dockerfile` 及相关文档更新，无任何可能影响构建基础设施的修改。CI 日志中前置检查（文件变更检测、依赖安装、镜像规格校验）全部通过，进一步证明 PR 变更本身无问题。

建议在 CI 侧重试该 job 以排除临时性环境故障。

## 潜在风险
无（未做代码修改）