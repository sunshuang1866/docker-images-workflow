# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 软件源HTTP/2流中断
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR (err 2), dnf, No more mirrors to try

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile`:7-10（builder 阶段的 `dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的 x86_64 OS 软件仓库的 HTTP/2 连接不稳定，多个 RPM 包（gcc-gfortran、glibc-devel、guile、gcc）在下载过程中遭遇 `Curl error (92): Stream error in the HTTP/2 framing layer`，最终 gcc（34 MB，体积最大的依赖包）在经历多次镜像重试后仍失败，dnf 报错退出。同时运行的 stage-1（#7）轻量包安装也遭遇了同类错误（glibc-devel、gcc-gfortran），但部分通过重试成功，最终因 builder 失败被 CANCELED。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 新增的 Dockerfile 本身语法正确、`dnf install` 包名均有效。失败完全由 openEuler 24.03-LTS-SP4 上游软件仓库的网络基础设施不稳定导致，属于 CI 运行时的瞬时基础设施故障。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复，触发 CI 重试即可。** 该故障为 openEuler 24.03-LTS-SP4 软件仓库的 HTTP/2 服务端间歇性问题，属于瞬时基础设施故障。在仓库服务恢复稳定后重新触发 CI 构建，大概率可以成功通过。可在 Jenkins 中对本次 PR 执行 "重试" 操作重新触发构建。

### 方向 2（置信度: 低，仅当反复重试仍然失败时考虑）
若多次重试后该仓库的 HTTP/2 连接问题持续存在，可考虑在 Dockerfile 的 `dnf install` 命令中添加 `--setopt=retries=10` 增加 dnf 内部重试次数，提升对间歇性网络波动的容忍度。但此方向仅作为兜底手段，当前更可能是仓库端的临时故障。

## 需要进一步确认的点
1. 确认 openEuler 24.03-LTS-SP4 的 OS 软件仓库当前是否稳定——可通过在 CI 环境中单独执行 dnf install 测试该仓库的可达性。
2. 确认同类镜像（如已有的 `cb37c53-oe2403sp3` 对应 24.03-lts-sp3 仓库）在同一时间段是否也出现类似网络问题，以判断是 SP4 仓库特有故障还是全线仓库波动。

## 修复验证要求
本次失败为 infra-error，无需代码修复。若后续触发重试仍然失败，需验证 openEuler 24.03-LTS-SP4 OS 仓库的 HTTP/2 服务端健康状况。
