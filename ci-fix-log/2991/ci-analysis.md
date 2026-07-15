# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: SP4仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, repo.openeuler.org, guile, dnf install

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
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6` — `RUN dnf install -y git gcc gcc-c++ make cmake && dnf clean all`
- 失败原因: 在 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）上，dnf 从 `repo.openeuler.org/openEuler-24.03-LTS-SP4` 仓库下载 156 个 RPM 包时，至少 3 个包（`git-core`、`gcc-c++`、`guile`）的下载因 HTTP/2 流层错误（Curl error 92）中断，其中 `guile` 在所有重试均失败后导致整个 dnf 事务失败（exit code: 1）。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 仅新增了 `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile` 及其元数据文件，Dockerfile 中的 `dnf install` 命令语法完全正确（与仓库中同类 SP3/SP4 Dockerfile 的写法一致）。失败根因是 CI 构建环境（aarch64 runner）访问 openEuler SP4 包仓库时遇到 HTTP/2 流层网络错误，属于基础设施层面的不稳定问题。

值得注意的是：
- 日志中部分包下载成功（如 `gcc` 30MB 耗时 7 分 55 秒、`git-core` 11MB 后续重试成功），说明网络并非完全不可达，而是特定连接流存在间歇性故障
- `gcc-c++` 两次在不同 HTTP/2 stream（stream 39 和 51）上均失败，暗示该特定连接的 HTTP/2 多路复用层面存在持续性问题
- 所有失败的包均来自 `repo.openeuler.org/openEuler-24.03-LTS-SP4` 仓库，且均为 aarch64 架构

## 修复方向

### 方向 1（置信度: 中）
**重试即可**。这是一种暂态网络故障，HTTP/2 流层错误通常由 CDN/反向代理与客户端之间的连接不稳定导致。最简单的处理方式是重新触发 CI 构建，如果网络恢复正常则构建会通过。不涉及任何代码修改。

### 方向 2（置信度: 低）
**在 Dockerfile 中增强重试机制**。如果此模式在 SP4 aarch64 构建中反复出现，可以考虑在 dnf 命令中增加重试次数来容忍间歇性网络错误。例如在 `dnf install` 命令中添加 `--setopt=retries=10` 或类似的 dnf 重试配置。但这是规避手段而非根治方案。

## 需要进一步确认的点
1. 同期是否有其他 PR 的 aarch64 SP4 构建（同 runner `ecs-build-docker-aarch64-04-sp`）也出现相同错误？如果多个 PR 均受影响，进一步确认这是基础设施问题而非本 PR 特有问题
2. `repo.openeuler.org/openEuler-24.03-LTS-SP4` 仓库在出问题时段是否发生过网络/CND 事件？
3. 重新触发 CI 构建后是否仍然复现？如不复现则确认为暂态网络波动
