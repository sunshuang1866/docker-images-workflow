# 修复摘要

## 修复的问题
CI 基础设施故障：openEuler 24.03-LTS-SP4 软件仓库镜像在构建期间出现 HTTP/2 协议层流中断错误（Curl error 92），导致 `gcc-c++` 等 RPM 包下载失败，`dnf install` 退出。

## 修改的文件
无需修改任何代码文件。CI 失败的根因是 openEuler 官方镜像仓库的网络层 HTTP/2 协议问题，与 PR #2980 提交的代码无关。

## 修复逻辑
- 失败类型为 `infra-error`，属于 CI 基础设施问题而非代码缺陷。
- Dockerfile 的 `RUN dnf install` 命令语法正确，与同项目已有的 sp3 版本 Dockerfile 模式一致。
- 3 个不同 RPM 包（`cmake-data`、`git-core`、`gcc-c++`）在下载过程中各自遭遇独立的 HTTP/2 stream 中断，说明是镜像站端的协议处理异常。
- 修复方向：重新触发 CI 构建。等待 openEuler 仓库镜像 HTTP/2 服务恢复后，CI 流水线应能正常通过。

## 潜在风险
无