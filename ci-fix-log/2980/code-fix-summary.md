# 修复摘要

## 修复的问题
无需代码修改。CI 失败由 openEuler 24.03-LTS-SP4 软件包仓库镜像的 HTTP/2 协议层流中断错误（`Curl error (92): Stream error in the HTTP/2 framing layer`）导致 `gcc-c++` 包下载失败，属于间歇性 CI 基础设施/网络层面的问题，与 PR 代码变更无关。

## 修改的文件
无（infra-error，无需修改代码）

## 修复逻辑
分析报告确认：
- `gcc-c++`（13MB）在 HTTP/2 传输过程中因 `INTERNAL_ERROR (err 2)` 流中断，`dnf` 在所有镜像重试后仍失败
- 同类错误（`cmake-data`、`git-core`）在重试后均成功下载，说明仓库本身可用，问题出在传输链路
- Dockerfile 中的 `dnf install` 命令正确，PR 仅新增了正确的构建配置
- 推荐操作：重试 CI 构建

## 潜在风险
无