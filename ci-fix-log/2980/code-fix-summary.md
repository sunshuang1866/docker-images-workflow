# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施问题（infra-error），由 openEuler 24.03-LTS-SP4 仓库镜像站的 HTTP/2 连接异常导致，与 PR #2980 的代码变更无关。

## 修改的文件
无（没有修改任何文件）

## 修复逻辑
CI 构建在 `dnf install` 步骤中，从 `repo.****.org` 下载 RPM 包时多次遭遇 `Curl error (92): Stream error in the HTTP/2 framing layer`（HTTP/2 流被服务端异常中断）。`cmake-data` 和 `git-core` 重试后成功下载，但 `gcc-c++` 连续两次失败后耗尽所有镜像重试，导致 dnf 安装步骤整体失败。

该 PR 新增的 Dockerfile 语法正确，`dnf install` 命令中的包名均有效（258 个包、914 MB 下载清单已成功解析）。失败完全由上游仓库镜像站的服务端连接问题造成，属于临时性 CI 基础设施故障。修复方向：重新触发 CI 构建即可。

## 潜在风险
无