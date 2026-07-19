# 修复摘要

## 修复的问题
CI 基础设施故障（infra-error）：BuildKit 构建器实例在 `dnf install` 下载元数据阶段被优雅关闭（`graceful_stop`），导致传输连接中断。与 PR 代码变更无关，无需修改代码。

## 修改的文件
无（infra-error，无需代码修改）

## 修复逻辑
根据 CI 失败分析报告，失败根因为 BuildKit 构建器实例 `euler_builder_20260709_224657` 被意外终止，属于 CI 基础设施层面的问题。PR #2994 仅新增了 scann 1.4.2 在 openEuler 24.03-lts-sp4 上的 Dockerfile 及配套元数据文件，Dockerfile 内容为标准模式，`dnf install` 安装的均为 openEuler 仓库中的常规包，不存在拼写错误或不存在的包名。构建失败发生在下载元数据阶段（尚未进入包安装和 Python 编译），与 Dockerfile 内容无因果关系。

修复方式：无需修改任何代码，直接重新触发 CI pipeline（re-run）即可。

## 潜在风险
无