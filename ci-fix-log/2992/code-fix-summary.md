# 修复摘要

## 修复的问题
无需代码修改。CI 失败原因为 openEuler 24.03-LTS-SP4 仓库镜像在构建时间窗口内出现 HTTP/2 协议层临时故障（Curl error 92），导致 RPM 包下载失败。

## 修改的文件
无（infra-error，非代码问题）

## 修复逻辑
CI 分析报告确认：
- Dockerfile 中 `dnf install` 命令语法和包名均正确
- 两个并行构建阶段（builder #8 和 stage-1 #7）同时遭遇相同 HTTP/2 流错误，说明是服务端/网络层问题
- PR 仅新增格式正确的 Dockerfile 及配套元数据文件，失败与 PR 代码变更无关

建议操作：重新触发 CI 构建即可。若同一镜像仓库反复出现该问题，可考虑在 `dnf` 命令前添加 `echo "http2=false" >> /etc/dnf/dnf.conf` 禁用 HTTP/2。

## 潜在风险
无