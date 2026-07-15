# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 软件源HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1268.5 [MIRROR] glibc-devel-2.38-107.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/glibc-devel-2.38-107.oe2403sp4.x86_64.rpm [HTTP/2 stream 17 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1598.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/guile-2.2.7-6.oe2403sp4.x86_64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7`（`dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的软件源镜像 `repo.****.org` 在通过 HTTP/2 协议下载大型 RPM 包（gcc 34MB、gcc-gfortran 13MB、guile 6.3MB、glibc-devel 2MB）时反复出现 HTTP/2 流错误（`Curl error (92)`），在多次重试耗尽所有镜像后，dnf 安装失败。

### 与 PR 变更的关联
与 PR 变更**无关**。PR 仅新增了 multiwfn 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及元数据文件，Dockerfile 本身的 `dnf install` 命令语法正确、包名有效。多个 RPM 包均出现相同的 HTTP/2 流错误说明这是 openEuler 24.03-LTS-SP4 软件仓库镜像的网络服务端问题，而非构建逻辑或代码错误。

值得注意的是，stage-1（运行时阶段 #7）也遇到了相同的 HTTP/2 流错误（`glibc-devel`、`gcc-gfortran` 等包），但通过 dnf 自动重试成功恢复了。builder 阶段（#8）因 `gcc` 包（34MB，最大的单个包）反复失败最终耗尽所有镜像导致构建中断。stage-1 随后被标记为 `CANCELED`（因 builder 阶段失败）。

## 修复方向

### 方向 1（置信度: 高）
**重试触发 CI**。这是 `infra-error`，根源是 openEuler 24.03-LTS-SP4 的软件源镜像在 CI 构建时段出现 HTTP/2 服务端异常，与 PR 代码无关。等待镜像站恢复稳定后重新触发 CI 流水线即可。

## 需要进一步确认的点
- openEuler 24.03-LTS-SP4 的 `repo.****.org` 镜像站在 CI 构建时段（2026-07-09 14:47 左右）是否存在已知的 HTTP/2 服务中断或性能问题
- 该镜像是否已恢复正常；若未恢复，可考虑在 Dockerfile 中为 dnf 添加 `--setopt=timeout=300` 等超时/重试参数以增强容错
- `#7`（stage-1）中 `glibc-devel` 也出现了相同错误但最终重试成功，说明该问题是间歇性的，进一步佐证为基础设施问题
