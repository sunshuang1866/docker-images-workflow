# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, err 2, repo.openeuler.org

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
------
ERROR: failed to solve: process "/bin/sh -c dnf install -y git gcc gcc-c++ make cmake && dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`
- 失败原因: aarch64 构建节点在 `dnf install` 阶段从 `repo.openeuler.org` 下载 RPM 包时，HTTP/2 连接反复出现流错误（`Curl error (92): Stream error in the HTTP/2 framing layer ... INTERNAL_ERROR (err 2)`），多个包（git-core、gcc-c++、guile）均受影响。最终 `guile` 软件包耗尽所有镜像源重试后下载失败，导致整个 dnf 事务终止。

### 与 PR 变更的关联

**与 PR 变更无关。** 本次 PR 仅新增了一个标准的 Dockerfile（安装 git/gcc/gcc-c++/make/cmake，然后 clone vvenc 源码编译），`dnf install` 命令完全正确。失败的直接原因是 `repo.openeuler.org` 镜像仓库在构建时（2026-07-09 14:09 UTC）对 aarch64 架构的 HTTP/2 服务不稳定，多个 RPM 包下载时频繁出现 HTTP/2 stream INTERNAL_ERROR，属于 CI 基础设施端的临时性网络问题。

值得注意的是，构建日志显示该节点（`ecs-build-docker-aarch64-04-sp`）之前已经成功完成了镜像仓库元数据缓存检查（`Last metadata expiration check: 0:42:14 ago`），说明节点网络本身可达，但在实际下载大量包时 HTTP/2 连接出现了传输层面的错误。

## 修复方向

### 方向 1（置信度: 高）
**重试构建。** 这是典型的 CI 基础设施临时故障，`repo.openeuler.org` 的 HTTP/2 服务端在构建时间窗口内不稳定。无需对 Dockerfile 做任何修改。直接在 CI 中重新触发 aarch64 架构的构建任务即可，有很大概率成功通过。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 在 aarch64 架构上的 HTTP/2 服务是否已恢复稳定。
- 如果多次重试仍然失败，可以考虑在 Dockerfile 的 `dnf install` 命令前添加 `echo "http2=false" >> /etc/dnf/dnf.conf` 将 dnf 降级为 HTTP/1.1 下载（若 dnf 版本支持此配置项），或添加 `--setopt=retries=10` 增加重试次数以提高容错能力。
- 确认其他 aarch64 构建节点（如 `ecs-build-docker-aarch64-01-sp`、`ecs-build-docker-aarch64-02-sp` 等）是否也遇到同样问题，以判断是个别节点问题还是整个 `repo.openeuler.org` 的后端问题。
