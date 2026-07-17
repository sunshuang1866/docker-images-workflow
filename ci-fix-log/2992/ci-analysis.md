# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: DNF仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, No more mirrors to try, dnf install

## 根因分析

### 直接错误

```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/guile-2.2.7-6.oe2403sp4.x86_64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7`（builder 阶段的 `dnf install` 命令）
- 失败原因: openEuler 24.03-LTS-SP4 的 DNF 软件仓库在通过 HTTP/2 协议下载 RPM 包时反复出现 `Stream error in the HTTP/2 framing layer`（Curl 错误码 92），多次重试后仍失败，`gcc-12.3.1-110.oe2403sp4.x86_64.rpm` 最终耗尽所有镜像重试次数，导致 `dnf install` 以 exit code 1 失败。

备注：builder 阶段（`#8`）需安装 157 个 RPM 包（总下载大小 261 MB），下载量大，遭遇了多次 HTTP/2 流错误（`gcc-gfortran` 2 次、`guile` 1 次、`gcc` 1 次），最终 `gcc` 包无法从任何镜像成功下载而彻底失败。最终阶段（`#7`，仅 32 个包）同样遭遇了 HTTP/2 流错误（`glibc-devel`、`gcc-gfortran`），但通过重试成功恢复，随后在 builder 阶段失败后被取消。

### 与 PR 变更的关联

**与 PR 改动无关。** PR #2992 的变更内容是：
- 新增 `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile`（47 行，标准的 dnf install + git clone + make 流程）
- 更新 `meta.yml`、`README.md`、`image-info.yml` 添加 SP4 版本条目

Dockerfile 本身的内容正确无语法错误，`dnf install` 命令中列出的包名均有效（与 SP3 版本完全一致的包名）。失败根因是 openEuler 24.03-LTS-SP4 软件仓库服务器的 HTTP/2 协议层存在间歇性流错误，属于 CI 基础设施/镜像站问题，非 PR 代码缺陷。

## 修复方向

### 方向 1（置信度: 中）
该失败为仓库侧 HTTP/2 协议问题，可通过以下任一方式规避：
- **重试构建**：该问题表现为间歇性（最终阶段 `#7` 的重试成功下载了大部分包），可能是临时性的仓库波动，直接重新触发 CI 构建可能通过。
- **DNF 配置降级到 HTTP/1.1**：在 Dockerfile 的 `dnf install` 前配置 DNF 使用 HTTP/1.1 协议以规避 HTTP/2 流错误，例如 `RUN echo "http2=false" >> /etc/dnf/dnf.conf` 或在基础镜像层面修复。
- **增加 DNF 重试次数**：在 `dnf install` 命令中添加 `--setopt=retries=10` 提高重试次数以抵抗间歇性流错误。

### 方向 2（置信度: 低）
openEuler 24.03-LTS-SP4 仓库的 HTTP/2 流错误可能是该仓库的已知问题，需联系仓库运维人员排查服务端 HTTP/2 实现。如果该问题持续存在且影响多个 PR，建议将规避方案（如配置 http2=false）统一纳入项目的基础镜像或 CI 构建模板中。

## 需要进一步确认的点
1. 该 openEuler 24.03-LTS-SP4 仓库的 HTTP/2 流错误是临时性波动还是持续性问题——建议查看同时间段其他使用 SP4 基础镜像的 PR 构建结果，或直接重新触发本次构建以验证。
2. 仓库地址在日志中被遮蔽（`repo.****.org`），需确认实际仓库域名以排查是否为特定镜像站的问题（不同镜像站可能有不同表现）。
3. 如果问题持续复现，需确认 DNF 是否支持配置禁用 HTTP/2（`http2=false`），以及该配置在 openEuler 基础镜像中的实际可用性。
