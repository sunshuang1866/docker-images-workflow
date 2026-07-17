# 修复摘要

## 修复的问题
无需代码修改。CI 失败由 openEuler 24.03-LTS-SP4 软件仓库镜像的 HTTP/2 传输层间歇性流错误（Curl error 92: INTERNAL_ERROR）导致，属于 CI 基础设施故障（infra-error），与 PR 变更无关。

## 修改的文件
无

## 修复逻辑
分析报告确认：Dockerfile 中的 `dnf install` 命令语法正确、包名有效。两个构建阶段（builder 的 #8 和 stage-1 的 #7）均因 `repo.****.org` 的 HTTP/2 流错误导致 RPM 包下载失败，属于服务端基础设施问题。PR 仅新增了 Multiwfn 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及配套元数据文件，不包含任何导致此错误的代码。建议待仓库镜像恢复后重新触发 CI 构建。

## 潜在风险
无