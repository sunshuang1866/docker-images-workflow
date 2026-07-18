# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施故障（infra-error），BuildKit builder 实例被 `graceful_stop` 信号提前终止，与 PR 代码变更无关。

## 修改的文件
无。本次为 infra-error，所有 PR 文件无需修改。

## 修复逻辑
CI 失败发生在 Docker 构建步骤 `[2/4]`（`dnf install` 阶段），BuildKit builder（`euler_builder_20260709_224657`）在执行包安装过程中被 `graceful_stop` 信号终止，导致 gRPC 传输连接断开（`connection error: EOF`）。该失败发生在依赖安装阶段，尚未执行到任何与 PR 具体内容相关的步骤（如 Python 编译或 scann 安装）。Dockerfile 语法和依赖声明均无问题。

修复方向：应在 CI 平台重新触发该 workflow/job，让构建在可用的 builder 实例上重新运行。若重试依然在同一步骤失败，需联系 CI 基础设施团队排查 builder 节点稳定性或 dnf 下载源连通性。

## 潜在风险
无。未修改任何代码。