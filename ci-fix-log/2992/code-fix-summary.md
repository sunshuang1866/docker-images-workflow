# 修复摘要

## 修复的问题
无需代码修复 — 此失败为 CI 基础设施问题（infra-error），非代码缺陷。

## 修改的文件
无

## 修复逻辑
CI 分析报告明确诊断为 `infra-error`：构建过程中 `dnf install` 从 openEuler 24.03-LTS-SP4 软件仓库下载 RPM 包时，仓库镜像服务器反复出现 HTTP/2 流的 `INTERNAL_ERROR`（Curl error 92），导致 gcc、gcc-gfortran、guile 等大型包下载中断，最终 gcc 包耗尽所有重试机会使构建失败。

该问题与 PR 变更无关——Dockerfile 语法和包名均正确，`dnf` 已成功解析依赖关系（157 个包均在仓库元数据中存在）。stage-1（运行阶段）的 `dnf install` 也遭遇同类错误，进一步佐证是仓库侧 HTTP/2 协议栈问题。

**修复方向**：等待 openEuler 24.03-LTS-SP4 软件仓库镜像恢复稳定后重新触发 CI 构建即可。

## 潜在风险
无