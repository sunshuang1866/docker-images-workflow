# 修复摘要

## 修复的问题
无代码修改。CI 失败为基础设施问题（BuildKit 构建器 `euler_builder_20260709_224657` 在 Docker 构建过程中意外断连），与 PR 代码变更无关。

## 修改的文件
无

## 修复逻辑
根据 CI 失败分析报告，失败发生在 Docker 构建步骤 `RUN dnf install -y gcc gcc-c++ make wget ...` 期间，错误为 `rpc error: code = Unavailable desc = closing transport due to: connection error: ... "graceful_stop"`。这是 BuildKit builder 实例被意外终止导致的基础设施故障，dnf 正在下载 metadata 时连接断开，并非 dnf 命令本身报错。该 PR 仅新增了 `Others/scann/1.4.2/24.03-lts-sp4/Dockerfile` 并更新了配套元数据文件，构建尚未到达任何可能由 PR 代码触发的错误阶段。

**无需修改代码**，建议重新触发 CI job。

## 潜在风险
无