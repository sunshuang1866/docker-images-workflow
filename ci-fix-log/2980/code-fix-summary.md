# 修复摘要

## 修复的问题
无需代码修改。CI 失败为 `infra-error`：openEuler 24.03-LTS-SP4 RPM 软件源镜像站在 HTTP/2 协议层面出现间歇性故障（Curl error 92: INTERNAL_ERROR err 2），导致部分包下载失败。

## 修改的文件
无

## 修复逻辑
根据 CI 失败分析报告，此次失败与 PR #2980 的代码变更无关。Dockerfile 中 `dnf install` 命令的语法和包名完全正确，258 个包均通过依赖解析，下载阶段因镜像站 HTTP/2 协议异常才报错。3 个不同包（cmake-data、git-core、gcc-c++）均遭遇相同的 `HTTP/2 stream INTERNAL_ERROR`，属于典型的服务端基础设施故障。

建议在镜像站恢复后重新触发 CI 构建。

## 潜在风险
无