# 修复摘要

## 修复的问题
无需代码修改。CI 失败是由 openEuler 24.03-LTS-SP4 仓库镜像的 HTTP/2 流层瞬时故障（Curl error 92）导致 `dnf install` 下载 `gcc-c++` 包失败，属于 CI 基础设施层面的网络/协议问题，与 PR 代码变更无关。

## 修改的文件
无（infra-error，不需要修改任何代码文件）

## 修复逻辑
1. 直接错误为 `Curl error (92): Stream error in the HTTP/2 framing layer`，出现在 `dnf install` 下载 RPM 包阶段。
2. Dockerfile 中 `RUN dnf install` 命令语法正确，所列软件包均为有效包名（dnf 已成功解析全部 258 个依赖并开始下载，38 个包成功下载后才在 `gcc-c++` 上失败）。
3. 三个包（`cmake-data`、`git-core`、`gcc-c++`）均短暂遭遇 HTTP/2 流错误，前两者重试后成功，仅 `gcc-c++` 两次重试均失败。
4. 此失败与 PR 代码变更**完全无关**，属于 infra-error 类型，应通过重新触发 CI 构建（Rerun）来验证和解决。

## 潜在风险
无。未修改任何代码，不存在引入新问题的风险。如果该问题反复出现，建议从 CI 侧排查仓库镜像 HTTP/2 服务稳定性或网络链路质量。