# 修复摘要

## 修复的问题
无需代码修改。该 CI 失败为 **infra-error**（基础设施问题），与 PR 代码变更无关。

## 修改的文件
无

## 修复逻辑
CI 失败的直接原因是 openEuler 24.03-LTS-SP4 的 RPM 镜像仓库（`repo.****.org`）在多个 HTTP/2 连接上间歇性返回流层错误（Curl error 92: `INTERNAL_ERROR`），导致 `gcc-c++` 等包的下载重试耗尽后失败。PR 仅新增了 GrADS 2.2.3 的 Dockerfile 及元数据更新，Dockerfile 中的 `dnf install` 命令语法正确、包名无错误。该失败完全由镜像仓库服务端的 HTTP/2 连接异常导致，属于临时性基础设施问题，与代码无关。

## 潜在风险
无。建议在镜像仓库恢复正常后重新触发 CI 构建。