# 修复摘要

## 修复的问题
无需代码修改。该失败属于 **infra-error**（CI 基础设施问题）——openEuler 24.03-LTS-SP4 软件仓库镜像在通过 HTTP/2 协议提供 RPM 包时出现流错误（Curl error 92: HTTP/2 stream INTERNAL_ERROR），导致 `gcc-c++` 等较大文件下载失败。Dockerfile 内容（包列表、configure 参数等）与 sp3 版本一致，写法正确，与 PR 代码变更**无直接关系**。

## 修改的文件
无。

## 修复逻辑
CI 失败分析报告明确指出失败类型为 `infra-error`，根因为 openEuler 24.03-LTS-SP4 仓库镜像的 HTTP/2 协议兼容性问题，属于外部基础设施故障，不在代码层面可控。

**建议的缓解措施**（如需在代码层面规避，可参考）：
- 在 `dnf install` 之前添加 `echo "http2=false" >> /etc/dnf/dnf.conf`，强制 dnf 使用 HTTP/1.1 下载，规避 HTTP/2 流错误。
- 或直接重试 CI job，HTTP/2 流错误可能是仓库镜像临时的协议层故障，下一次构建可能不再复现。

## 潜在风险
如果后续决定添加 `http2=false` 到 dnf 配置中，需注意该配置会影响该 Dockerfile 中所有 dnf 下载操作，回退到 HTTP/1.1 可能会导致下载速度略有下降。除此之外无其他风险。