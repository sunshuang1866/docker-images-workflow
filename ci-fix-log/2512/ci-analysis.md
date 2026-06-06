# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 模式18
- 新模式标题: （不适用）
- 新模式症状关键词: （不适用）

## 根因分析

### 直接错误
（CI 日志仅包含 trigger pipeline 输出，未包含 x86-64 / aarch64 子 job 的实际构建日志。trigger pipeline 自身以 SUCCESS 完成，但两个架构的子构建 job 均报告 FAILURE。以下分析基于 PR diff 与历史模式匹配。）

子 job 失败状态：
```
multiarch » openeuler » x86-64 » openeuler-docker-images #1357 completed. Result was FAILURE
multiarch » openeuler » aarch64 » openeuler-docker-images #1332 completed. Result was FAILURE
```

### 根因定位
- 失败位置: `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile:21-23`
- 失败原因: `git clone --depth 1` 创建浅克隆（仅包含最新提交），后续 `git checkout ${VERSION}` 尝试检出特定 commit hash（`22fca04`）失败，但被 `2>/dev/null || true` 静默掩盖，导致构建使用了错误的源码。

### 与 PR 变更的关联
PR 新增了 `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`，其中第 21-23 行包含以下致命模式：

```dockerfile
git clone --recurse-submodules --depth 1 --shallow-submodules https://github.com/deepseek-ai/3fs /tmp/3fs && \
git -C /tmp/3fs checkout ${VERSION} 2>/dev/null || true && \
git -C /tmp/3fs submodule update --init --recursive --depth 1 2>/dev/null || true && \
```

- `--depth 1` 只拉取默认分支的最新一次提交
- `ARG VERSION=22fca04` 指向一个历史 commit hash
- 该 commit hash 不在浅克隆的本地历史中，`git checkout ${VERSION}` 必然失败
- `2>/dev/null || true` 吞噬了 checkout 的错误信息，构建继续使用错误的源码（默认分支 HEAD）
- 子模块更新同样使用 `2>/dev/null || true` 掩码，子模块状态也不正确

此 PR 的 Dockerfile 已被历史知识库明确收录为 **模式18** 的典型案例。

### 附加发现

1. **`meson install` 错误掩码** (`Dockerfile:16`)
   - `meson install -C build 2>/dev/null || true` 同样静默抑制了 fuse3 安装阶段可能的失败，若 fuse3 安装不完整会影响 3FS 的链接和运行。

2. **版权声明缺失**（警告级，非阻断）
   - CI license check 报告 `缺少项目级Copyright声明文件`，新增文件（Dockerfile、README.md、image-info.yml、meta.yml）均未包含 Copyright + SPDX-License-Identifier 头。

## 修复方向

### 方向 1（置信度: 高）
将 `git clone --depth 1` + `git checkout ${VERSION} 2>/dev/null || true` 替换为完整的 fetch + checkout 流程。先执行 `git clone`（不含 `--depth 1`），再正常 `git checkout ${VERSION}`，**去掉 `2>/dev/null || true` 掩码**，使 checkout 失败能暴露为构建错误而非静默继续。若需保持浅克隆优势，可在 checkout 前先 `git fetch origin ${VERSION}` 按需获取目标 commit。

### 方向 2（置信度: 中）
将 `meson install -C build 2>/dev/null || true` 中的 `2>/dev/null || true` 移除，或改为 `|| echo "WARNING: meson install failed"` 使其可见，便于排查 fuse3 安装问题是否也导致了构建失败。

### 方向 3（置信度: 中）
为 `Dockerfile`、`README.md`、`doc/image-info.yml`、`meta.yml` 等新增文件添加 Copyright 和 SPDX-License-Identifier 声明头（参考模式17）。

## 需要进一步确认的点
1. x86-64 和 aarch64 子 job 的实际构建日志未提供，无法从日志中直接确认错误信息（如 cmake configure 失败的具体报错）。建议从 Jenkins 获取 `#1357` 和 `#1332` 的完整构建日志以验证诊断。
2. 上游仓库 `deepseek-ai/3fs` 的 commit `22fca04` 是否仍然是默认分支历史可访问的提交，需确认 fetch 该 commit 是否成功。
3. openEuler 24.03-LTS-SP3 仓库中 `gflags-devel`、`glog-devel`、`gtest-devel`、`gmock-devel`、`libuv-devel` 等包名的确切拼写是否与 Dockerfile 中一致，需在容器内验证 yum install 是否全部成功。
