# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流中断
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1268.5 [MIRROR] glibc-devel-2.38-107.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/glibc-devel-2.38-107.oe2403sp4.x86_64.rpm [HTTP/2 stream 17 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ...
#7 1598.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ...
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ...
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ...
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（builder 阶段的 `dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 官方仓库镜像在 CI 构建时出现 HTTP/2 协议层流错误（Curl error 92: INTERNAL_ERROR），导致多个 RPM 包（gcc-gfortran、glibc-devel、guile、gcc）下载中断。其中 `gcc` 包（34 MB）因体积较大，在所有镜像重试后仍然下载失败，触发 `dnf install` 整体失败。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 本次 PR 仅新增了 multiwfn 在 openEuler 24.03-LTS-SP4 上的 Dockerfile（47 行）及配套的 README、image-info.yml、meta.yml 更新。Dockerfile 的 `dnf install` 命令语法和包名均正确，与已有的 sp3 版本 Dockerfile 模式一致。失败原因是 CI 构建时 openEuler SP4 仓库镜像的网络/协议层不稳定，属于基础设施问题。

两个并行构建阶段（`#7` stage-1 和 `#8` builder）均遭遇了同一仓库的 HTTP/2 流错误，进一步证实问题出在仓库端而非 Dockerfile 配置。

## 修复方向

### 方向 1（置信度: 高）
**等待 CI 基础设施恢复后重新触发构建。** 此失败为 openEuler 24.03-LTS-SP4 仓库镜像的临时性 HTTP/2 协议故障，与 PR 代码无关。无需修改任何 Dockerfile 或配置文件。建议在仓库镜像恢复稳定后手动 re-run 该 CI job。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 仓库镜像（`repo.****.org`）在 CI 构建时间段是否存在已知的服务中断或 HTTP/2 协议问题。
- 若多次重试后仍然失败，可能需要确认 CI 构建节点的网络代理/VPN 配置是否对 SP4 仓库的 HTTP/2 连接造成干扰，或考虑在 `dnf install` 前添加 `echo "http2=false" >> /etc/dnf/dnf.conf` 临时禁用 HTTP/2 作为规避手段。
- 确认同一 CI 环境中其他使用 openEuler 24.03-LTS-SP4 基础镜像的构建是否也出现类似问题（若普遍出现，则确认为仓库端问题）。

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
无需填写。本次失败为 infra-error，不涉及正则 patch 或代码修改。
