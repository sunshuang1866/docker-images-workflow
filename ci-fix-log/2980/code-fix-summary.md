# 修复摘要

## 修复的问题
无需代码修复。CI 失败是由 openEuler 24.03-LTS-SP4 官方仓库镜像的 HTTP/2 协议临时不稳定导致的 `infra-error`（Curl error 92: HTTP/2 stream INTERNAL_ERROR），与 PR 代码变更无关。

## 修改的文件
无。Dockerfile 中 `dnf install` 命令语法正确，所列软件包名称均有效，无需修改任何文件。

## 修复逻辑
分析报告明确指出此为临时性基础设施故障：
- 3 个 RPM 包（cmake-data、git-core、gcc-c++）下载时均出现 HTTP/2 stream 错误
- cmake-data 和 git-core 重试后成功，仅 gcc-c++（13 MB）两次尝试均失败导致 DNF 放弃
- 修复方向（置信度高）：重新触发 CI 构建即可

## 潜在风险
无。未对代码做任何修改。