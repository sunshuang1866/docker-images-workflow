# 修复摘要

## 修复的问题
无需代码修改 — 分析报告指出的两个问题在 SP4 Dockerfile 中已修复。

## 修改的文件
无需修改。`Bigdata/kyuubi/1.11.1/24.03-lts-sp4/Dockerfile` 当前版本已包含两项修复：

1. **Kyuubi 下载源切换**（第 17 行）：已从 `downloads.apache.org` 切换为 `dlcdn.apache.org`。已通过 WebFetch 验证 `https://dlcdn.apache.org/kyuubi/kyuubi-1.11.1/apache-kyuubi-1.11.1-bin.tgz` 可正常访问（返回二进制内容，非 404）。
2. **BUILDARCH 变量冲突修复**（第 29 行）：RUN 步骤中的变量已重命名为 `JAVA_ARCH`，避免与 BuildKit 预定义 `BUILDARCH` 全局 ARG 冲突。

## 修复逻辑
对比 SP3 版本 Dockerfile（仍使用 `downloads.apache.org` 和 `BUILDARCH`）与 SP4 版本，SP4 版本在提交前已正确应用了模式33（下载源切换）和模式09（BuildKit 变量冲突）的修复，与 PR #2105 对 SP3 的修复方案一致。

## 潜在风险
无