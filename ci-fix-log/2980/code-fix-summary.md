# 修复摘要

## 修复的问题
无代码修改。CI 失败为 openEuler 24.03-LTS-SP4 软件仓库服务器端 HTTP/2 协议临时故障（`Curl error 92: Stream error in the HTTP/2 framing layer`），属于基础设施临时问题，非 PR #2980 代码变更导致。

## 修改的文件
无

## 修复逻辑
CI 分析报告明确指出失败类型为 `infra-error`，根因为 openEuler 24.03-LTS-SP4 仓库的 HTTP/2 服务端协议临时故障（`INTERNAL_ERROR` 来自服务端主动关闭流），导致 `dnf install` 下载 gcc-c++ 等 RPM 包时多次重试失败。PR 仅新增了标准的 Dockerfile 及配套元数据文件，Dockerfile 中的包名均合法且仓库中真实存在（DNF 成功解析了 258 个包的依赖关系）。此问题与代码无关，触发 CI 重试即可。

## 潜在风险
无