# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: openEuler仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, repo.openeuler.org, aarch64, yum install, Error downloading packages

## 根因分析

### 直接错误

```
#7 1310.2 [MIRROR] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm [HTTP/2 stream 125 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1310.2 [FAILED] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1310.3 Error: Error downloading packages:
#7 1310.3   vim-common-2:9.0.2092-36.oe2403sp4.aarch64: Cannot download, all mirrors were already tried without success
#7 ERROR: process "/bin/sh -c yum install -y ..." did not complete successfully: exit code: 1
```

在此之前，另有 3 个包也遭遇了同类网络错误但重试后下载成功：
- `gcc-12.3.1-110.oe2403sp4.aarch64.rpm`: Curl error (92)，重试成功
- `kernel-headers-6.6.0-159.4.3.154.oe2403sp4.aarch64.rpm`: Curl error (92)，重试成功
- `perl-MIME-Base64-3.16-2.oe2403sp4.aarch64.rpm`: Curl error (56)，重试成功

### 根因定位
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（`RUN yum install -y` 步骤）
- 失败原因: CI 构建节点（`ecs-build-docker-aarch64-04-sp`，aarch64）在从 `repo.openeuler.org` 下载 `vim-common` 包时遭遇 HTTP/2 传输流错误（Curl error 92），yum 耗尽所有重试后放弃。整个构建过程中共有 4 个包（173 个中的 4 个）遭遇同类网络异常，前 3 个重试成功，`vim-common` 最终失败。

### 与 PR 变更的关联

**与 PR 变更无关。** 本次 PR 仅新增以下文件：
1. `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile` — 新增 Dockerfile，`yum install` 安装的包均为 openEuler SP4 仓库标准包
2. `Others/brpc/README.md` — 文档更新
3. `Others/brpc/doc/image-info.yml` — 镜像信息更新
4. `Others/brpc/meta.yml` — 元数据新增条目

Dockerfile 的 `yum install` 命令语法和包列表均正确，失败根因是 aarch64 构建节点访问 `repo.openeuler.org` 时发生的网络层 HTTP/2 传输错误（Curl error 92），属 CI 基础设施侧的瞬态网络故障。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建。** 这是典型的 CI 基础设施瞬态网络故障——openEuler 官方仓库 `repo.openeuler.org` 的 aarch64 镜像节点在短时间内出现 HTTP/2 流中断。证据是同一个构建过程中 173 个包中的 169 个下载成功，仅 4 个遭遇 Curl 错误且其中 3 个重试后成功。重新运行 CI Job 大概率可恢复正常。

### 方向 2（置信度: 低）
如果多次重试仍然失败，可能是 `repo.openeuler.org` 的 aarch64 镜像在特定时段持续不稳定。此时可考虑在 Dockerfile 的 `yum install` 前添加 `yum-config-manager` 配置，或添加 `--retries` / `--setopt` 参数增加 yum 重试次数和超时时间，以提升对瞬态网络波动的容忍度。**但鉴于本次仅 1/173 的包彻底失败，极大概率只需重试 CI 即可。**

## 需要进一步确认的点
- 确认 `vim-common-2:9.0.2092-36.oe2403sp4.aarch64` 在 `repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/` 中确实存在（从日志看该包在 yum 解析阶段被列出，说明仓库元数据中已登记，应确实存在，故此项仅为形式确认）
