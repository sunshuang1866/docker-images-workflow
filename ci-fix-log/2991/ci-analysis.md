# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), HTTP/2 stream, INTERNAL_ERROR (err 2), repo.openeuler.org, dnf install

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
- 失败原因: `dnf install` 从 `repo.openeuler.org` 下载 aarch64 架构 RPM 包时，多个包（git-core、gcc-c++、guile）遭遇 HTTP/2 协议层 stream 错误（Curl error 92），最终 `guile` 包因所有镜像源均已尝试但均失败（HTTP/2 错误耗尽重试次数），导致整个安装步骤退出码为 1。

### 与 PR 变更的关联
**与 PR 改动无直接关联**。PR 仅新增一个标准的 Dockerfile（安装 git/gcc/gcc-c++/make/cmake，克隆 vvenc 源码并编译），Dockerfile 本身语法正确、逻辑合理。失败发生在 `dnf install` 从 openEuler 官方仓库下载 RPM 包阶段，属于 CI 构建环境与 `repo.openeuler.org` 之间的 HTTP/2 协议层通信问题。`git-core` 和 `gcc-c++` 经历了 HTTP/2 错误后通过重试（换镜像）成功下载，但 `guile` 耗尽所有镜像重试后仍然失败。

具体来看：
- `git-core` 在第 1273.6s 遭遇 HTTP/2 错误后，于第 1513.9s 重试成功
- `gcc-c++` 在第 1419.8s 和第 1548.4s 两次遭遇 HTTP/2 错误，说明 dnf 的镜像重试机制在起作用，但 HTTP/2 问题持续性存在
- `guile` 是最终耗尽重试次数而失败的那个包，根因并非 `guile` 包本身有问题

## 修复方向

### 方向 1（置信度: 中）
**触发 CI 重试**。该失败属于 openEuler 官方仓库 `repo.openeuler.org` 的 HTTP/2 协议层临时性问题（Curl error 92: HTTP/2 stream not closed cleanly），与 PR 代码无关。建议直接重新触发 CI 运行，等待仓库服务恢复后即可通过。

### 方向 2（置信度: 低）
**在 Dockerfile 中为 dnf 添加 HTTP/1.1 回退**。如果仓库持续存在 HTTP/2 问题，可在 Dockerfile 的 `dnf install` 前设置环境变量禁用 HTTP/2（如 `echo "http2=false" >> /etc/dnf/dnf.conf`），强制 dnf 使用 HTTP/1.1 下载。但此方案仅为 workaround，且需确认 HTTP/1.1 下仓库可达。

## 需要进一步确认的点
1. `repo.openeuler.org` 的 HTTP/2 CDN/代理服务在构建时段是否存在已知的稳定性问题
2. 同一时段其他 SP4 aarch64 构建（如 PR 中的其他镜像）是否也遭遇同样的 HTTP/2 stream 错误，以判断是普遍基础设施问题还是个别网络波动
3. 重试 CI 后该失败是否消失——如果消失，则确认是临时性基础设施故障，无需任何代码修改
