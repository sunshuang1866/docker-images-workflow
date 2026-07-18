# 修复摘要

## 修复的问题
无需代码修复。CI 失败为基础设施错误（infra-error），由 openEuler 24.03-LTS-SP4 仓库镜像站 HTTP/2 协议层间歇性错误（Curl error 92: Stream error in the HTTP/2 framing layer）导致 `dnf install` 下载 RPM 包失败，与 PR 代码变更无关。

## 修改的文件
无

## 修复逻辑
分析报告确认：Dockerfile 中 `dnf install` 命令语法正确，所列依赖包在仓库中均存在（Dependencies resolved 阶段列出所有 258 个包）。cmake-data 和 git-core 在重试后成功下载，说明问题为瞬时性网络抖动。推荐操作：触发 CI 重新运行该 job。

## 潜在风险
无