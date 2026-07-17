# 修复摘要

## 修复的问题
无需代码修复。CI 失败原因为 BuildKit builder 实例 `euler_builder_20260709_224657` 在 Docker 构建过程中被提前终止（`graceful_stop`），属于 CI 基础设施瞬时故障。

## 修改的文件
无

## 修复逻辑
根据 CI 失败分析报告，这是一次 **infra-error**：
- 失败位置在 Docker 构建阶段 `dnf install` 下载 OS 元数据时，BuildKit builder 实例被调度器回收（GOAWAY + `graceful_stop`）。
- PR 变更仅涉及 `Others/scann/1.4.2/24.03-lts-sp4/Dockerfile` 及元数据文件的常规新增，Dockerfile 内容无语法错误或依赖缺失问题。
- 日志中 `dnf install` 下载速度极慢（77 kB/s），推测 builder 所在节点网络不佳触发了超时回收机制。

**推荐操作**：重新触发 CI 运行。若反复出现同一问题，需排查 CI 环境中 `euler_builder_*` 实例的超时配置或网络质量。

## 潜在风险
无