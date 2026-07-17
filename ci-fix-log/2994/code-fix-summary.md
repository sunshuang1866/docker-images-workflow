# 修复摘要

## 修复的问题
无需代码修改。此为 CI 基础设施临时故障（infra-error），BuildKit 构建器 `euler_builder_20260709_224657` 在 `dnf install` 下载仓库元数据时被优雅关闭（`graceful_stop`），导致 gRPC 连接中断。

## 修改的文件
无

## 修复逻辑
CI 失败分析报告指向 `infra-error` 类型，根因是 BuildKit builder 实例被外部原因终止（GracefulStop），与 PR #2994 的代码变更无因果关系：
- 新增的 Dockerfile 语法正确
- `dnf install` 列出的包名（`gcc gcc-c++ make wget openssl-devel bzip2-devel zlib-devel`）均为 openEuler 24.03-LTS-SP4 仓库的标准可用包
- 失败发生在 dnf 下载元数据阶段，而非编译或安装阶段

建议重新触发 CI 流水线。若反复出现，应由 CI 运维团队排查 builder 节点的资源配置和超时策略。

## 潜在风险
无