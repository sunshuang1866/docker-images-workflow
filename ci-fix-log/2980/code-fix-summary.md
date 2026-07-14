# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施问题（infra-error）：openEuler 24.03-LTS-SP4 仓库在 CI 运行时段出现 HTTP/2 流传输故障，导致部分大型 RPM 包（gcc-c++）下载失败。PR 新增的 Dockerfile 语法和包列表均正确无误。

## 修改的文件
无（infra-error，非代码缺陷）

## 修复逻辑
根据 CI 失败分析报告，失败类型为 `infra-error`，置信度高。根因是 openEuler 仓库端 HTTP/2 连接不稳定（`Curl error (92): Stream error in the HTTP/2 framing layer`），同类包 `cmake-data` 在重试后成功，说明仓库可访问但连接间歇性失败。Dockerfile 内容正确，不需要任何代码修改。建议等待仓库恢复后重新触发 CI 构建。

## 潜在风险
无