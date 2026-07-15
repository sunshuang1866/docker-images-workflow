# 修复摘要

## 修复的问题
无需代码修改。CI 构建失败为 openEuler 24.03-LTS-SP4 软件仓库镜像站的 HTTP/2 协议栈间歇性错误（`Curl error (92): Stream error in the HTTP/2 framing layer`，服务端报 `INTERNAL_ERROR (err 2)`），属于基础设施故障。

## 修改的文件
无代码修改。

## 修复逻辑
分析报告明确指出：构建失败与 PR 代码变更无关，Dockerfile 中 `dnf install` 步骤所列依赖包列表语法正确、包名合法，依赖解析成功（日志显示 "258 Packages" 和 "Installed size: 1.3 G"）。失败根因是 dnf 从 openEuler 24.03-LTS-SP4 仓库下载 RPM 包时，仓库服务器返回 HTTP/2 协议层流错误，导致 `gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm` 经历两次流中断后下载失败。建议通过重试 CI（re-run the failed job）解决，或待仓库镜像站恢复后再次触发构建。

## 潜在风险
无。