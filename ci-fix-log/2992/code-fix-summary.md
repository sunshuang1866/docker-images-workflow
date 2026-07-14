# 修复摘要

## 修复的问题
无需代码修改。该 CI 失败属于 **infra-error**（基础设施问题），是 openEuler 24.03-LTS-SP4 仓库镜像 (`repo.****.org`) 的 HTTP/2 协议层间歇性错误（Curl error 92: INTERNAL_ERROR），导致 `dnf install` 下载 RPM 包失败。

## 修改的文件
无

## 修复逻辑
CI 分析报告明确指出：Dockerfile 本身的语法和 `dnf install` 包列表均无问题，失败根因是仓库镜像在构建时段的 HTTP/2 不稳定，属于基础设施问题，与 PR 代码变更无关。

**建议操作**：直接 re-run CI。stage-1 最终成功恢复表明该问题为间歇性，重新触发构建有较高概率通过。

如果连续多次重试后仍失败，可考虑在 Dockerfile 的 `dnf install` 之前添加 `RUN echo "http2=false" >> /etc/dnf/dnf.conf` 强制 dnf 使用 HTTP/1.1 下载。

## 潜在风险
无