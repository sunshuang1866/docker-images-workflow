# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: build-error
- 置信度: 中
- 知识库匹配: 模式18 + 模式20
- 新模式: 否

## 根因分析

### 直接错误
CI 日志中**缺失 x86-64 和 aarch64 下游构建 job 的实际构建日志**。提供的日志仅包含触发 job（trigger），显示：
```
multiarch » openeuler » x86-64 » openeuler-docker-images #1357 completed. Result was FAILURE
multiarch » openeuler » aarch64 » openeuler-docker-images #1332 completed. Result was FAILURE
```
触发 job 自身以 SUCCESS 结束，但下游两个架构的 Docker 构建 job 均失败。**具体构建报错信息不可见**。

### 根因定位
- 失败位置: `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile:28-30`（推断）
- 失败原因: `git clone --depth 1` 浅克隆后无法 checkout 指定 commit hash `22fca04`，且错误被 `2>/dev/null || true` 静默掩盖，导致构建使用了错误的源码版本（默认分支 HEAD 而非指定 commit），触发下游编译/链接失败

### 与 PR 变更的关联
本次 PR 新增了 `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`，其中第 28-30 行存在两处问题：

1. **浅克隆与 commit hash checkout 冲突**：`git clone --recurse-submodules --depth 1` 只拉取最新一次提交，随后 `git -C /tmp/3fs checkout ${VERSION}`（VERSION=22fca04，为一个 commit hash）尝试切换到一个不在浅克隆对象范围内的历史提交，checkout 必然失败。

2. **错误被静默掩盖**：`git -C /tmp/3fs checkout ${VERSION} 2>/dev/null || true` 中的 `|| true` 使 checkout 失败后构建继续，但实际代码并未切换到目标版本 22fca04，导致后续 `cmake` 构建阶段使用了错误的上游代码，最终在两个架构均编译失败。

历史知识库（模式18）已记录此 PR 的相同问题，确认为 `--depth 1` + commit hash checkout 不兼容导致。

## 修复方向

### 方向 1（置信度: 高）
将 `git clone --depth 1` 改为完整克隆（去掉 `--depth 1`），确保 commit hash `22fca04` 在本地仓库中可访问，使 `git checkout ${VERSION}` 能正确切换。同时去掉 `2>/dev/null || true` 的错误抑制，让 checkout 失败时构建立即终止，避免静默使用错误代码。

### 方向 2（置信度: 中）
保留 `--depth 1` 浅克隆，但在 checkout 前先执行 `git -C /tmp/3fs fetch --depth 1 origin ${VERSION}` 将目标 commit 拉取到本地，再执行 `git checkout ${VERSION}`，并去掉 `|| true` 错误抑制。

## 需要进一步确认的点
1. x86-64 和 aarch64 下游构建 job 的**完整构建日志**（含 Docker build 输出），以确认具体编译错误信息是否与 git checkout 失败导致的源码版本不一致相符
2. commit `22fca04` 相对于 deepseek-ai/3fs 默认分支 HEAD 的差异范围，以评估源码版本不一致可能引发的构建失败类型
3. `--shallow-submodules` 在 submodule 上下文中的行为是否也影响了子模块的正确检出
