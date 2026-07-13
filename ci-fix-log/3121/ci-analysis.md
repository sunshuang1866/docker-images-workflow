# CI 失败分析报告

## 基本信息
- PR: #3121 — chore(claude-code): add openEuler 24.03-LTS-SP4 support
- 失败类型: dependency-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 外部安装脚本403拒绝
- 新模式症状关键词: curl: (22), 403, install.sh, claude.ai

## 根因分析

### 直接错误
```
#9 [3/7] RUN curl -fsSL "https://claude.ai/install.sh" -o /tmp/claude-install.sh && \
    chmod +x /tmp/claude-install.sh && \
    /tmp/claude-install.sh "2.1.20" && \
    rm -f /tmp/claude-install.sh
#9 0.313 curl: (22) The requested URL returned error: 403
#9 ERROR: process "/bin/sh -c curl -fsSL \"${CLAUDE_INSTALL_SCRIPT}\" -o /tmp/claude-install.sh && ..." did not complete successfully: exit code: 22
```

### 根因定位
- 失败位置: `AI/claude-code/2.1.20/24.03-lts-sp4/Dockerfile:16-19`（Docker 构建第 3/7 步）
- 失败原因: Dockerfile 中硬编码的 `curl -fsSL "https://claude.ai/install.sh"` 被 Anthropic 服务器返回 HTTP 403，CI 构建环境无法下载安装脚本。基础镜像拉取（第 1 步）和 yum 安装（第 2 步）均正常完成，问题仅出在外部 URL 下载环节。

### 与 PR 变更的关联
**直接关联**。PR 新增的 `AI/claude-code/2.1.20/24.03-lts-sp4/Dockerfile` 是全新文件，其中第 10 行 `ARG CLAUDE_INSTALL_SCRIPT="https://claude.ai/install.sh"` 和第 16 行的 `curl -fsSL "${CLAUDE_INSTALL_SCRIPT}"` 直接触发了此失败。该 Dockerfile 是本次 PR 新增的唯一构建文件，问题完全由本次变更引入。

## 修复方向

### 方向 1（置信度: 中）
`claude.ai/install.sh` 可能对非浏览器 User-Agent 有访问限制，导致 curl 默认请求头被拒绝。可尝试在 `curl` 命令中添加浏览器模拟请求头（如 `-H "User-Agent: Mozilla/5.0"`），绕过服务器的 bot 检测。但此方案依赖 Anthropic 的服务器策略，不一定有效。

### 方向 2（置信度: 中）
`claude.ai/install.sh` 的安装脚本 URL 可能已变更或不再支持直接下载。需要验证：
- `https://claude.ai/install.sh` 在当前是否仍然有效（在非 CI 环境的浏览器/anonymous 终端中测试）
- Anthropic 是否提供了新的安装方式或替代下载 URL
- 同仓库中已存在的 `AI/claude-code/2.1.20/24.03-lts-sp3/Dockerfile` 是否使用了相同 URL，以及当前构建是否也失败（若是，说明上游 URL 已全局失效）

### 方向 3（置信度: 低）
CI 构建环境的出口 IP 可能被 `claude.ai` 列入黑名单或受到地域限制。如果方向 1 和方向 2 均无法解决，需联系 CI 运维团队确认构建节点的网络出口策略是否被目标服务阻断。

## 需要进一步确认的点
1. 同仓库中已有的 `AI/claude-code/2.1.20/24.03-lts-sp3/Dockerfile` 是否使用相同的 `https://claude.ai/install.sh`，其最近一次构建是否也失败（确认是 URL 全局失效还是偶然性问题）
2. 从非 CI 环境（本地终端）执行 `curl -fsSL "https://claude.ai/install.sh"` 是否能正常下载（确认是环境限制还是 URL 变更）
3. Anthropic 官方文档中 `install.sh` 的当前有效 URL 是什么（确认上游是否迁移了安装入口）
4. `claude-code` 2.1.20 版本是否仍然受支持，该版本在 sp4 上的兼容性是否已经过验证
