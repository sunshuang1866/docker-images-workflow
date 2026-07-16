# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, repo.openeuler.org

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
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y git gcc gcc-c++ make cmake && dnf clean all`）
- 失败原因: CI 在 aarch64 runner 上构建时，`dnf install` 从 `repo.openeuler.org` 下载多个 RPM 包（git-core、gcc-c++、guile）过程中遭遇 HTTP/2 流错误（Curl error 92: INTERNAL_ERROR），所有镜像源重试均失败，最终 `guile` 包下载失败导致 `dnf` 退出码为 1。这是 openEuler 镜像仓库服务端的 HTTP/2 协议层间歇性故障，与 PR 代码变更完全无关。

### 与 PR 变更的关联
- **PR 改动与失败无关**。此次 PR 仅新增了一个标准的 vvenc Dockerfile（安装 git、gcc、gcc-c++、make、cmake 后编译 vvenc），同时更新了 README.md、image-info.yml 和 meta.yml。Dockerfile 中 `dnf install` 命令本身语法正确，构建在基础镜像拉取成功后才开始，失败完全由 `repo.openeuler.org` 镜像仓库的网络/协议层故障导致。
- 日志中显示共有 3 个包出现 HTTP/2 流错误（git-core、gcc-c++ 两次、guile），其中 git-core 和 gcc-c++ 在重试后可能成功下载，但 guile 在所有镜像源均失败后导致整个 dnf 事务回滚。
- 构建发生在 `ecs-build-docker-aarch64-04-sp (docker-build-aarch64)` 节点，问题仅限于 aarch64 架构的包下载阶段。

## 修复方向

### 方向 1（置信度: 高）
**重试触发 CI 构建**。这是一个临时性的基础设施故障（`repo.openeuler.org` 的 HTTP/2 服务端在构建时出现流中断），PR 代码本身无需修改。直接重新触发 CI 流水线，大概率可以成功通过。如果多次重试仍失败，则需联系 openEuler 镜像仓库运维团队排查 `repo.openeuler.org` 的 HTTP/2 服务端稳定性问题。

### 方向 2（置信度: 低）
**在 Dockerfile 中添加 dnf 下载重试**。虽然这是 infra-error，但可考虑在 `dnf install` 命令中添加 `--setopt=retries=10` 或在 RUN 前用 shell 循环包裹以提高鲁棒性。但这并非必要修复，因为正常情况下镜像仓库不存在此类问题。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 在构建时间点是否有已知的服务降级或维护事件。
- 确认 aarch64 架构的 x86-64 对应 job（如果存在）是否也遇到相同的 HTTP/2 流错误，以判断是全局性问题还是仅 aarch64 镜像源受影响。

## 修复验证要求
不适用（infra-error，无需代码修改）。
