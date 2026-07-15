# 修复摘要

## 修复的问题
此 CI 失败为基础设施故障（BuildKit builder 断连），无需代码修改。

## 修改的文件
无（infra-error，不涉及代码变更）

## 修复逻辑
CI 分析报告确认：失败发生在 Docker 构建步骤 `#7 [2/4] RUN dnf install` 执行期间，BuildKit 构建器实例 `euler_builder_20260709_224657` 异常断开连接（gRPC 报 `Unavailable` + `graceful_stop`），属于 CI runner 基础设施故障。构建在 dnf 下载 metadata 阶段（尚未开始安装具体包）时 builder 断连，与 PR 代码变更无关。

PR 新增的 `Others/scann/1.4.2/24.03-lts-sp4/Dockerfile` 语法正确，`dnf install` 中列出的包均为 openEuler 仓库标准包，无需任何修改。

建议直接重新触发 CI 构建（re-run）。

## 潜在风险
无