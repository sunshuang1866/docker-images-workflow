# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像 HTTP/2 流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install

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
#8 ERROR: process "/bin/sh -c dnf install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（`dnf install` 步骤，builder 阶段）
- 失败原因: openEuler 24.03-LTS-SP4 的软件仓库镜像（`repo.****.org`）在处理 HTTP/2 请求时频繁出现流协议错误（`Curl error (92): Stream error in the HTTP/2 framing layer`），导致 `gcc`、`gcc-gfortran`、`glibc-devel`、`guile` 等多个 RPM 包下载均因服务端 `INTERNAL_ERROR` 而失败，dnf 在尝试所有镜像后放弃。

### 与 PR 变更的关联
与 PR 变更无关。本次 PR 仅新增了 multiwfn 在 openEuler 24.03-lts-sp4 上的 Dockerfile（以及配套的 README、meta.yml、image-info.yml 元数据更新），Dockerfile 内容与已有的 sp3 版本结构一致，无语法错误或逻辑问题。失败完全由 openEuler 24.03-LTS-SP4 仓库镜像的 HTTP/2 服务端不稳定导致。此外，stage-1 阶段（`#7`）在尝试下载同样来自 SP4 仓库的包时也遇到了相同的 HTTP/2 流错误（`glibc-devel`、`gcc-gfortran`），进一步证明问题是仓库侧基础设施问题，而非 PR 代码所致。

## 修复方向

### 方向 1（置信度: 低）
重试 CI 构建。该错误为 openEuler 24.03-LTS-SP4 仓库镜像的间歇性 HTTP/2 服务端故障，与 PR 代码无关，重新触发 CI 构建大概率可以通过。

### 方向 2（置信度: 低）
若多次重试均失败，可尝试在 Dockerfile 的 `dnf install` 之前配置 dnf 禁用 HTTP/2、强制使用 HTTP/1.1（如设置 `http2=false` 或设置环境变量降低 curl 协议版本），绕过仓库镜像的 HTTP/2 实现缺陷。但这属于绕过方案，根本原因是仓库侧的服务端 bug。

## 需要进一步确认的点
- 确认 `repo.****.org` 的 openEuler-24.03-LTS-SP4 仓库在当前时间段是否已知存在 HTTP/2 服务端问题（可联系 openEuler 镜像站运维确认）
- 确认该 PR 的 aarch64 构建 job 是否同样失败（日志中仅包含 x86-64 job 的输出）
- 确认同一时间段内其他引用 openEuler 24.03-lts-sp4 基础镜像的 PR 是否也出现了相同错误（以排除特定包文件的损坏）
