# 修复摘要

## 修复的问题
无代码修复 —— 此 CI 失败为 **infra-error**（基础设施错误），与 PR 代码变更无关。

## 修改的文件
无（无需修改任何文件）

## 修复逻辑
CI 失败的直接原因是 `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6` 行 `dnf install -y ...` 步骤中，从 openEuler 24.03-LTS-SP4 软件仓库（`repo.****.org`）下载 RPM 包时遭遇 HTTP/2 流错误（Curl error 92）：
- 多个包（`cmake-data`、`git-core`、`gcc-c++`）出现 `Stream error in the HTTP/2 framing layer: INTERNAL_ERROR (err 2)`
- `gcc-c++` 两次重试均失败，DNF 耗尽所有镜像重试，导致构建失败

根因是上游 openEuler 24.03-LTS-SP4 RPM 仓库服务器的 HTTP/2 实现存在协议层问题（stream 异常关闭），属于临时性基础设施故障。PR #2980 仅新增了 Dockerfile 及配套配置文件，Dockerfile 内容本身无语法或逻辑错误，构建失败与代码变更完全无关。

**无需任何代码修改**。等待上游仓库的 HTTP/2 服务恢复后，重新触发 CI 构建即可通过。

## 潜在风险
无