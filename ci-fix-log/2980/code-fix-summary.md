# 修复摘要

## 修复的问题
无需代码修复。CI 失败为基础设施层面的网络问题，与 PR 代码无关。

## 修改的文件
无代码修改。

## 修复逻辑
CI 失败的直接原因是 `dnf install` 阶段从 `repo.****.org`（openEuler 24.03-LTS-SP4 软件仓库）下载 RPM 包时，HTTP/2 连接反复出现 `Curl error (92): Stream error in the HTTP/2 framing layer: INTERNAL_ERROR`。多个不同包（`cmake-data`、`git-core`、`gcc-c++`）均遭遇同样的错误，最终 `gcc-c++` 包重试耗尽所有镜像后下载失败。

分析报告确认：Dockerfile 语法正确，`dnf install` 声明的所有包名均为 openEuler 24.03-LTS-SP4 仓库中真实存在的包，258 个包均被 dnf 成功识别并进入下载阶段。失败发生在网络下载层，属于 openEuler 软件仓库镜像在构建时段的 HTTP/2 服务不稳定问题。

**结论**：这是 `infra-error`，等待仓库镜像恢复后触发 CI 重试（re-run failed job）即可。若该问题持续出现，建议联系 openEuler 基础设施团队排查仓库镜像的 HTTP/2 服务端配置。

## 潜在风险
无。未做任何代码修改。