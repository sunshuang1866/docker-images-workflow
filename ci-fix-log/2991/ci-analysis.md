# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: DNF仓库HTTP2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install, repo.openeuler.org

## 根因分析

### 直接错误

```
#7 1273.6 [MIRROR] git-core-2.54.0-2.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/git-core-2.54.0-2.oe2403sp4.aarch64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]

#7 1419.8 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 39 was not closed cleanly: INTERNAL_ERROR (err 2)]

#7 1548.4 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 51 was not closed cleanly: INTERNAL_ERROR (err 2)]

#7 1709.6 [MIRROR] guile-2.2.7-6.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/guile-2.2.7-6.oe2403sp4.aarch64.rpm [HTTP/2 stream 49 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [FAILED] guile-2.2.7-6.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1709.7 Error: Error downloading packages:
#7 ERROR: process "/bin/sh -c dnf install -y git gcc gcc-c++ make cmake && dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位

- 失败位置: Dockerfile:6（新增文件 `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile`）
- 失败原因: CI 构建节点（aarch64）在执行 `dnf install` 从 `repo.openeuler.org` 下载依赖包时，多个包的 HTTP/2 传输流被服务端异常关闭（`INTERNAL_ERROR`），其中 `guile-2.2.7-6.oe2403sp4.aarch64.rpm` 重试耗尽所有镜像后彻底失败，导致整个 Docker 构建中断。

### 与 PR 变更的关联

**与 PR 无关。** PR #2991 的改动仅包括：
1. 新增 `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile`（13 行，标准构建流程：`dnf install` 基础工具 → `git clone` → `cmake` 构建）
2. 更新 `README.md` / `image-info.yml`（文档条目）
3. 更新 `meta.yml`（新增构建条目）

Dockerfile 中的 `dnf install -y git gcc gcc-c++ make cmake` 是常规软件包安装指令，语法和包名均正确。失败根因是 `repo.openeuler.org` 对外部请求的 HTTP/2 流返回 `INTERNAL_ERROR`（Curl error 92），属于服务端或网络中间件的协议层问题，与 PR 代码变更无关。重试即可通过。

## 修复方向

### 方向 1（置信度: 高）
触发 CI 重试（re-run）。该失败为 `repo.openeuler.org` 临时性的 HTTP/2 协议层错误，非代码问题，重新触发构建大概率可以通过。

### 方向 2（置信度: 低）
若多次重试仍持续失败，可考虑在 Dockerfile 的 `dnf install` 命令中增加 `--retries 10` 或添加 `--setopt=timeout=120` 等参数提高网络容错能力。但这属于治标方案，不建议在未确认上游仓库持续不稳定前采用。

## 需要进一步确认的点

- `repo.openeuler.org` 在 CI 构建时段（2026-07-09 14:09 UTC）是否存在已知的 HTTP/2 服务端问题或负载异常。
- 该 aarch64 构建节点（`ecs-build-docker-aarch64-04-sp`）到 `repo.openeuler.org` 的网络链路是否稳定。
