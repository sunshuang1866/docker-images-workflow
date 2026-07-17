# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: Repo HTTP/2 流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, dnf install, repo.openeuler.org

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
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`
- 失败原因: CI aarch64 构建节点在执行 `dnf install` 从 `repo.openeuler.org` 下载 RPM 包时，多个包（`git-core`、`gcc-c++`、`guile`）遭遇 HTTP/2 协议层流错误（Curl error 92: `Stream error in the HTTP/2 framing layer`），最终 `guile` 包因所有镜像源均尝试失败而导致整个 `dnf install` 命令退出码为 1。这是 openEuler 官方仓库服务器的 HTTP/2 实现问题或 CI 节点与仓库之间的网络协议兼容性问题，属于基础设施故障。

### 与 PR 变更的关联
**与 PR 变更无关。** 本次 PR 仅新增了一个标准的 vvenc 1.14.0 Dockerfile（安装 gcc/gcc-c++/cmake/make 构建工具，然后编译 vvenc）以及对应的 README.md、image-info.yml、meta.yml 元数据更新。Dockerfile 中 `dnf install` 的包列表完全正确，是 openEuler 系统仓库中的合法包名。失败完全由 `repo.openeuler.org` 镜像站 aarch64 SP4 仓库的 HTTP/2 下载服务端问题导致，无需修改任何 PR 代码。

## 修复方向

### 方向 1（置信度: 高）
**无需修改 PR 代码，等待 CI 重试。** 该失败是 `repo.openeuler.org` 镜像站 aarch64 SP4 仓库的 HTTP/2 传输层瞬时故障（`INTERNAL_ERROR`）。属于可自动恢复的基础设施问题。建议触发 CI 重新构建，大概率可通过。
- 若多次重试仍失败，可考虑在 Dockerfile 的 `dnf install` 前添加 `dnf makecache` 或换用其他 openEuler 镜像源（如 `mirrors.tuna.tsinghua.edu.cn`、`mirrors.ustc.edu.cn` 等）。

### 方向 2（可选，置信度: 低）
若该问题持续出现，可能是 CI aarch64 构建节点与 `repo.openeuler.org` 之间存在 HTTP/2 协议协商不兼容。可尝试在 Dockerfile 中的 `dnf install` 前设置环境变量强制 curl/libcurl 降级到 HTTP/1.1（通过 `/etc/dnf/dnf.conf` 或环境变量 `RPM_HTTP_VERSION=1.1`），或为 `dnf` 配置 `http2=false` 选项，绕过 HTTP/2 协议栈问题。

## 需要进一步确认的点
- `repo.openeuler.org` 针对 openEuler 24.03-LTS-SP4 aarch64 仓库在 CI 失败时间段是否有已知的 HTTP/2 服务端问题。
- 其他 PR 在同时段构建 aarch64 SP4 镜像时是否也出现了同样的 Curl error (92) 错误（若是，则可确认为仓库侧问题）。
- 之前已有的 vvenc SP3（`1.14.0-oe2403sp3`）以及其他 SP4 镜像在 aarch64 节点上是否能正常通过 `dnf install`（可对比确认是否仅为瞬时故障）。
