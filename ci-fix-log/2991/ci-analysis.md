# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: HTTP/2仓库流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing, INTERNAL_ERROR, dnf install, repo.openeuler.org

## 根因分析

### 直接错误
```
#7 1273.6 [MIRROR] git-core-2.54.0-2.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/git-core-2.54.0-2.oe2403sp4.aarch64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1419.8 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 39 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1548.4 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 51 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [MIRROR] guile-2.2.7-6.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/guile-2.2.7-6.oe2403sp4.aarch64.rpm [HTTP/2 stream 49 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [FAILED] guile-2.2.7-6.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1709.7 Error: Error downloading packages:
#7 1709.7   guile-5:2.2.7-6.oe2403sp4.aarch64: Cannot download, all mirrors were already tried without success
#7 ERROR: process "/bin/sh -c dnf install -y git gcc gcc-c++ make cmake && dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`
- 失败原因: 在 aarch64 runner 上执行 `dnf install` 时，`repo.openeuler.org` 的 openEuler 24.03-LTS-SP4 仓库反复返回 HTTP/2 流错误（Curl error 92: INTERNAL_ERROR），导致 `gcc-c++`、`git-core`、`guile` 三个 RPM 包下载失败，其中 `guile` 耗尽所有镜像重试后 dnf 安装整体失败。

### 与 PR 变更的关联
**与 PR 无关。** 本次 PR 仅新增了 vvenc 1.14.0 在 openEuler 24.03-lts-sp4 上的 Dockerfile（含 `dnf install` 标准构建依赖命令）以及配套的 README.md、image-info.yml、meta.yml 元数据更新，代码逻辑无缺陷。失败的根本原因是 `repo.openeuler.org` 的 aarch64 仓库在构建时（UTC 2026-07-09 14:09）存在 HTTP/2 服务端流错误，属于基础设施层面的临时性问题。

## 修复方向

### 方向 1（置信度: 高）
**重试构建。** 该类 `Curl error (92): Stream error in the HTTP/2 framing layer` 为 openEuler 官方仓库 `repo.openeuler.org` 的服务端 HTTP/2 协议层瞬时故障，与 PR 代码无关。重新触发 CI 构建即可（若仓库已恢复，相同代码应能通过）。

### 方向 2（置信度: 中）
**添加 dnf 重试机制。** 若此类问题频繁出现，可考虑在 Dockerfile 的 `dnf install` 命令中添加 `--setopt=retries=10` 参数或 `--allowerasing`，但这是优化性措施而非本次必须执行的修复。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 的 openEuler 24.03-LTS-SP4 aarch64 仓库当前是否已恢复稳定（可在重试前手动 `curl -I` 验证相关 RPM 包的 HTTP 状态）。
- 确认其他使用同一仓库路径的 Dockerfile（如同仓库下其他 24.03-lts-sp4 镜像）是否也出现类似失败，以判定这是否为仓库范围的系统性故障。

## 修复验证要求
无需验证（infra-error，无需修改任何代码文件）。
