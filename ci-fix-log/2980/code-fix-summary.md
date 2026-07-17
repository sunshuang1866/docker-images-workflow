# 修复摘要

## 修复的问题
无需代码修复。CI 失败原因为 openEuler 24.03-LTS-SP4 软件仓库（`repo.****.org`）的 HTTP/2 传输层间歇性故障（Curl error 92: INTERNAL_ERROR），属于 CI 基础设施问题（infra-error），与 PR 代码变更无关。

## 修改的文件
无

## 修复逻辑
分析报告确认：
- 失败发生在 `dnf install` 下载 RPM 包时，`cmake-data`、`git-core`、`gcc-c++` 因 HTTP/2 流错误（`Stream error in the HTTP/2 framing layer`）下载失败
- Dockerfile 中 `dnf install` 命令语法正确、依赖包列表完整，PR 变更不包含任何代码错误
- `cmake-data` 在重试后成功下载，印证是网络波动而非包不存在

根据工作流程规定，infra-error 类型失败不应修改代码，应触发 CI 重新运行。若多次重试仍失败，需联系 openEuler 基础设施团队排查仓库服务器 HTTP/2 兼容性问题。

## 潜在风险
无