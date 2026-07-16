# 修复摘要

## 修复的问题
无需代码修改。CI 失败为 `infra-error`（基础设施错误），由 CI 构建节点与 openEuler 24.03-LTS-SP4 软件包仓库之间的 HTTP/2 流帧错误（Curl error 92）导致 `gcc-c++` RPM 包下载失败，与 PR 代码变更无关。

## 修改的文件
无

## 修复逻辑
CI 失败分析报告明确指出：失败类型为 `infra-error`，根因是临时性网络基础设施问题（HTTP/2 流中断），Dockerfile 中 `dnf install` 的依赖包列表均属于 openEuler 24.03-LTS-SP4 仓库的常规可用包，不存在拼写错误或版本不存在的问题。按照指令要求，infra-error 类型的失败不做代码修改。建议重新触发 CI Job 即可。

## 潜在风险
无