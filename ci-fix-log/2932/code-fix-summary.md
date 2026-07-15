# 修复摘要

## 修复的问题
CI 失败属于基础设施故障（infra-error），与 PR 代码变更无关，无需代码修改。

## 修改的文件
无

## 修复逻辑
CI 失败发生在 BuildKit builder 初始化阶段（`[internal] booting buildkit`），Docker daemon 报告 `Could not find the file / in container`，此时 Dockerfile 指令尚未开始执行。PR 仅新增了 glibc 2.42 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及相关元数据文件，属于标准镜像新增操作，不可能触发此错误。这是 CI runner 上的 BuildKit builder 容器创建时的临时基础设施故障，建议直接重新触发 CI 构建（retry），此类瞬态错误通常不会连续出现。

## 潜在风险
无