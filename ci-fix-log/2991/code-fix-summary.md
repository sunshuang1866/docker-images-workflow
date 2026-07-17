# 修复摘要

## 修复的问题
无需代码修复。CI 失败为 infra-error（网络基础设施问题），与 PR 代码变更无关。

## 修改的文件
无。PR 代码无需任何修改。

## 修复逻辑
CI 失败根因为 openEuler 24.03-LTS-SP4 仓库服务器 `repo.openeuler.org` 在处理 aarch64 架构 RPM 包下载时返回 HTTP/2 流协议错误（Curl error 92: `INTERNAL_ERROR`），导致 `guile` 等包下载失败。该错误发生在 Dockerfile 第 6 行 `dnf install` 的纯网络下载层面，属于上游仓库服务器的临时性 HTTP/2 协议异常或网络波动。

PR 新增的 Dockerfile 语法和逻辑均正确：基础镜像拉取成功、`dnf install` 命令本身无误。其他已存在的 sp3 Dockerfile 使用相同的 `dnf install` 模式且正常运行，进一步证明失败与 PR 代码无关。

**建议操作：直接 re-run 该 CI job。** 此类 HTTP/2 流错误通常为间歇性问题，重试即可恢复。

若多次重试仍以相同方式失败，可以考虑在 Dockerfile 中降级到 HTTP/1.1（如在 `dnf install` 前执行 `echo 'http2=false' >> /etc/dnf/dnf.conf`），但当前证据不支撑此结论。

## 潜在风险
无。未对任何代码进行修改。