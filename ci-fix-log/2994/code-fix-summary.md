# 修复摘要

## 修复的问题
无需代码修复。CI 失败原因为基础设施问题：BuildKit builder 实例 `euler_builder_20260709_224657` 在 `dnf install` 下载 OS 元数据阶段被服务端主动关闭（`graceful_stop`），与 PR #2994 的代码变更无关。

## 修改的文件
无

## 修复逻辑
CI 分析报告明确判定为 **infra-error**，置信度高。失败发生在 Docker 构建步骤 `#7 [2/4] RUN dnf install`，此时尚未执行任何与 scann 或 Python 编译相关的操作。PR #2994 仅新增 `Others/scann/1.4.2/24.03-lts-sp4/Dockerfile` 及配套元数据文件，不会触发 BuildKit builder 的 `graceful_stop`。修复方向：重试 CI 构建即可。

## 潜在风险
无