# 修复摘要

## 修复的问题
无需代码修改。CI 构建失败为 openEuler 24.03-LTS-SP4 官方仓库（`repo.****.org`）的间歇性 HTTP/2 服务端故障（Curl error 92: INTERNAL_ERROR），属于基础设施问题（infra-error），与 PR #2980 的代码变更无关。

## 修改的文件
无

## 修复逻辑
CI 在执行 `dnf install` 从 openEuler 24.03-LTS-SP4 仓库下载 `gcc-c++` RPM 包时，仓库服务器端 HTTP/2 连接出现 INTERNAL_ERROR，导致下载失败。该 PR 仅新增了 Dockerfile 及文档更新，Dockerfile 语法正确，`dnf install` 依赖列表无问题。待仓库服务恢复后重新触发 CI 构建即可通过。

## 潜在风险
无