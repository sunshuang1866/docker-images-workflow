# 修复摘要

## 修复的问题
无需代码修改。CI 失败类型为 `infra-error`，根因是 openEuler 24.03-LTS-SP4 镜像站在 HTTP/2 传输层反复出现流错误（Curl error 92: HTTP/2 stream INTERNAL_ERROR），导致 `dnf install` 下载 `gcc-c++`、`cmake-data`、`git-core` 三个 RPM 包失败。

## 修改的文件
无（未修改任何文件）

## 修复逻辑
CI 分析报告明确指出此失败为基础设施/网络层问题，与 PR #2980 的代码变更无关。PR 仅新增了一个标准的 Grads Dockerfile 及配套元数据文件，Dockerfile 中的包列表与同仓库其他 Grads 版本一致，语法正确。失败发生在 `dnf` 从远程 RPM 仓库下载包阶段，属于下游镜像站网络传输问题。建议在 CI 中重试该构建任务。

## 潜在风险
无