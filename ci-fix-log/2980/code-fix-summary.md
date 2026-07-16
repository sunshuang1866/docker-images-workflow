# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施问题（infra-error），openEuler 24.03-LTS-SP4 RPM 仓库镜像 HTTP/2 协议层临时性故障导致包下载失败，与 PR #2980 的代码变更无关。

## 修改的文件
无

## 修复逻辑
CI 分析报告判定此失败为 `infra-error`，根因是 openEuler 24.03-LTS-SP4 的 RPM 仓库镜像在 HTTP/2 传输过程中出现流中断（Curl error 92: INTERNAL_ERROR），导致 `gcc-c++` 等包下载失败。该 Dockerfile 的 `dnf install` 命令语法和包列表均正确——依赖解析阶段已成功完成，失败仅发生在后续的实际下载阶段。属于瞬态网络问题，重新触发 CI 构建即可。若多次重试均失败，需排查 openEuler 24.03-LTS-SP4 仓库镜像的服务健康状态。

## 潜在风险
无