# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: dnf仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error, HTTP/2 framing layer, [MIRROR], No more mirrors to try, dnf install

## 根因分析

### 直接错误
```
#8 [builder 2/5] RUN dnf install -y git gcc gcc-c++ gcc-gfortran make openblas-devel lapack-devel && dnf clean all:
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/guile-2.2.7-6.oe2403sp4.x86_64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 Result: [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 Error: Error downloading packages:
#8   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#8 ERROR: process "/bin/sh -c dnf install -y ..." did not complete successfully: exit code: 1
------
Dockerfile:7
ERROR: failed to solve: process "/bin/sh -c dnf install -y git gcc gcc-c++ gcc-gfortran make openblas-devel lapack-devel && dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7`（`RUN dnf install -y ...` builder 阶段的包安装步骤）
- 失败原因: Docker 构建的 builder 阶段在通过 dnf 从 openEuler 24.03-LTS-SP4 仓库下载 RPM 包时，多个包（`gcc-gfortran`、`glibc-devel`、`guile`、`gcc`）遭遇 `Curl error (92): Stream error in the HTTP/2 framing layer`，即仓库服务器的 HTTP/2 协议层连接异常中断。dnf 重试了所有可用镜像后仍无法成功下载 `gcc-12.3.1-110.oe2403sp4.x86_64.rpm`，导致构建退出码 1。

### 与 PR 变更的关联
PR 变更**与此次失败无直接关联**。PR 的改动纯粹是：
1. 新增 `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile` — 为 openEuler 24.03-LTS-SP4 平台添加 multiwfn 应用镜像
2. 更新 `Others/multiwfn/meta.yml` — 注册新镜像版本条目
3. 更新 `Others/multiwfn/README.md` 和 `Others/multiwfn/doc/image-info.yml` — 文档同步

新增的 Dockerfile 内容语法正确，包名无误（与同仓库已有 SP3 版本结构一致），不存在任何可导致 HTTP/2 协议错误的代码问题。失败完全由 openEuler 24.03-LTS-SP4 软件源仓库的网络/协议层故障引起。

## 修复方向

### 方向 1（置信度: 高）
**重试 CI 构建**。此次失败是 openEuler 24.03-LTS-SP4 仓库服务器的 HTTP/2 基础设施问题（`INTERNAL_ERROR (err 2)` 表明服务端主动断开 HTTP/2 流），与 PR 代码无关。等待仓库服务恢复后重新触发 CI 构建即可通过。无需对 Dockerfile 做任何修改。

### 方向 2（置信度: 低，仅在重试多次仍失败时考虑）
若重试后持续失败，可能是 CI 构建环境的 curl/nghttp2 库与仓库服务器的 HTTP/2 实现存在兼容性问题。可尝试在 Dockerfile 的 `dnf install` 命令前添加 `echo "http2=false" >> /etc/dnf/dnf.conf` 或 `echo "max_parallel_downloads=1" >> /etc/dnf/dnf.conf` 来降低协议复杂度。但这只是临时绕过手段，不应作为最终方案。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 仓库（`repo.openeuler.org` 或配置的镜像站）在 CI 构建时段内是否存在网络抖动或 HTTP/2 服务降级
- 确认 CI runner（`ecs-build-docker-x86-03-sp`）的网络环境是否稳定，是否存在中间代理或防火墙对 HTTP/2 长连接有超时/干扰行为
- 若持续复现，可对比同仓库已有的 SP3 构建（使用 `repo.****.org/openEuler-24.03-LTS-SP3/`）是否也存在同样问题，以区分"SP4 仓库特有"还是"整个仓库服务波动"

## 修复验证要求
（无，本次失败为 infra-error，无需代码修复。重试 CI 即可。）
