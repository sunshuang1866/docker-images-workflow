# 修复摘要

## 修复的问题
无需代码修改。CI 失败原因为 openEuler 24.03-LTS-SP4 软件包仓库服务器的 HTTP/2 协议层不稳定（Curl error 92），属于 CI 基础设施/上游仓库的网络问题，与 PR 代码变更无关。

## 修改的文件
无

## 修复逻辑
CI 分析报告判定失败类型为 `infra-error`。失败发生在 `dnf install` 下载 GCC/gfortran/openblas 等包时，openEuler 24.03-LTS-SP4 仓库服务器在 HTTP/2 流传输中多次发送 `INTERNAL_ERROR` 并断开连接，导致大体积包（如 gcc 34MB）重试耗尽后失败。PR 新增的 Dockerfile 中 `dnf install` 命令写法与已有的 sp3 版本完全一致，代码本身无问题。根据规范，infra-error 不应强行修改代码。建议等待上游仓库恢复后重新触发 CI。

## 潜在风险
无