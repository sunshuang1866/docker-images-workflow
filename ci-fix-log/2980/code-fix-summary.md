# 修复摘要

## 修复的问题
无需代码修改。CI 失败属于 infra-error（基础设施错误），由 openEuler 24.03-LTS-SP4 镜像仓库服务器的 HTTP/2 传输层间歇性故障导致。

## 修改的文件
无

## 修复逻辑
CI 日志显示，`dnf install` 的依赖解析阶段已成功（258 个包全部解析），但下载过程中 `repo.****.org` 镜像站多次返回 `Curl error (92): Stream error in the HTTP/2 framing layer`（HTTP/2 流未正常关闭，INTERNAL_ERROR）。三个软件包（cmake-data、git-core、gcc-c++）受影响，前两者经过重试后恢复，但 gcc-c++ 两次尝试均失败，最终 dnf 耗尽所有镜像后报错退出。

PR 新增的 Dockerfile 中 `dnf install` 命令语法完全正确，所列软件包名称均为 openEuler 24.03-LTS-SP4 仓库中实际存在的有效包。失败与 PR 代码变更无关，属于上游镜像仓库服务器的瞬时基础设施问题。

**建议**：重新触发 CI 构建即可。

## 潜在风险
无