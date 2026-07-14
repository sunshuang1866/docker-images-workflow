# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2传输失败
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, MIRROR, No more mirrors to try, repo.openeuler.org

## 根因分析

### 直接错误
```
#8 [builder 2/5] RUN dnf install -y git gcc gcc-c++ gcc-gfortran make openblas-devel lapack-devel && dnf clean all
...
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#8 ERROR: process "/bin/sh -c dnf install -y git gcc gcc-c++ gcc-gfortran make openblas-devel lapack-devel && dnf clean all" did not complete successfully: exit code: 1
```

同样，#7（stage-1 最终镜像层）也遭遇了 `gcc-gfortran` 和 `glibc-devel` 的 HTTP/2 流错误，在 #8 失败后被 CANCELED。

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（`dnf install` 步骤）
- 失败原因: CI 构建节点在执行 `dnf install` 时，从 openEuler 24.03-LTS-SP4 软件仓库（`repo.****.org`，应为 `repo.openeuler.org`）下载 RPM 包时，服务端持续返回 HTTP/2 帧流错误（Curl error 92: INTERNAL_ERROR），导致 `gcc`、`gcc-gfortran`、`guile`、`glibc-devel` 等多个包下载失败，所有镜像重试耗尽后 dnf 退出码为 1，构建终止。

### 与 PR 变更的关联
**无关**。本次 PR 仅新增了以下文件，均为 openEuler 24.03-LTS-SP4 的标准适配工作：
- 新增 `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile`（新 Docker 镜像定义）
- 修改 `Others/multiwfn/README.md`（文档表增加 SP4 行）
- 修改 `Others/multiwfn/doc/image-info.yml`（镜像信息表增加 SP4 行）
- 修改 `Others/multiwfn/meta.yml`（元数据注册新 tag）

没有任何代码变更会触发 RPM 包下载的网络层故障。失败完全由 openEuler 软件仓库镜像的 HTTP/2 传输不稳定导致。

## 修复方向

### 方向 1（置信度: 高）
**重试 CI 构建**。该失败是 openEuler 24.03-LTS-SP4 软件仓库的临时性 HTTP/2 传输故障。CI 构建环境通过 dnf/curl 与仓库通信时，服务端的 HTTP/2 流协议层出现间歇性 `INTERNAL_ERROR`。此类基础设施问题通常可自行恢复，无需修改任何代码。若连续多次重试仍失败，需联系 openEuler 基础设施团队排查 `repo.openeuler.org` 的 HTTP/2 服务端稳定性。

## 需要进一步确认的点
- 确认 `repo.****.org` 实际指向 `repo.openeuler.org`，验证该仓库在构建时间窗口内是否存在已知故障或维护通知
- 观察同一时段其他使用 openEuler 24.03-LTS-SP4 基础镜像的 PR（如 aarch64 架构的构建 job）是否也报告了相同的 HTTP/2 流错误，以判断是偶发波动还是系统性仓库故障
