# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: dnf仓库HTTP/2协议错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, dnf, openEuler repo

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
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（builder 阶段的 `RUN dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的 RPM 软件仓库镜像在 HTTP/2 协议层面持续返回 `INTERNAL_ERROR`（Curl error 92），导致 `gcc`、`gcc-gfortran`、`glibc-devel`、`guile` 等多个 RPM 包下载失败。最终 `gcc` 包在所有已尝试的镜像上均失败（"No more mirrors to try"），dnf 安装整体失败并退出。

### 与 PR 变更的关联
PR 变更与此次失败无因果关系。PR 仅为 Multiwfn 新增了 openEuler 24.03-LTS-SP4 版本的支持（新增 Dockerfile 和更新元数据文件），Dockerfile 的 `dnf install` 命令本身语法和包名均正确（对比 stage-1 的 `dnf install` 已成功解析依赖并开始下载部分包即可确认）。失败由 CI 构建环境访问 SP4 仓库时遇到的 HTTP/2 协议级服务端错误导致，属于基础设施问题。

值得注意的是，stage-1（最终镜像阶段）的 `dnf install` 也遭遇了同样的 HTTP/2 流错误（`#7 1268.5` 和 `#7 1598.9` 两处），但 stage-1 最终因 builder 阶段失败而被 CANCELED，无法判断是否能自己恢复。这表明 SP4 仓库的 HTTP/2 问题并非针对特定包或请求的偶发现象，而是在同一时间段内影响了多次下载尝试。

## 修复方向

### 方向 1（置信度: 中）
重试 CI 构建。该问题可能是 openEuler 24.03-LTS-SP4 仓库镜像的临时性 HTTP/2 服务端故障，一段时间后可能自行恢复。从日志可见，builder 阶段 #8 在 1243.9s 第一次报 `gcc-gfortran` 的 HTTP/2 错误后，又在 1468.3s 和 1767.8s 继续出现同类错误，横跨约 7 分钟，说明故障有一定持续性，但不能排除为当天/当周仓库镜像的不稳定窗口期。

### 方向 2（置信度: 低）
若 SP4 仓库的 HTTP/2 问题持续无法恢复，可在 Dockerfile 的 `dnf install` 命令前添加配置禁用 HTTP/2，强制 dnf/libcurl 回退到 HTTP/1.1 协议。具体操作：在 `dnf install` 之前添加 `echo "http2=false" >> /etc/dnf/dnf.conf` 或 `RUN dnf config-manager --setopt=http2=false`，然后执行安装。不过该方案需验证 SP4 仓库在 HTTP/1.1 下是否稳定可用，且技术上将 HTTP/2 错误降级为 HTTP/1.1 并不解决仓库服务端的根本问题。

## 需要进一步确认的点
1. 重试 CI 构建后，SP4 仓库的 HTTP/2 错误是否消失（判断是临时故障还是持续性问题）。
2. openEuler 24.03-LTS-SP4 仓库镜像的运维状态，是否存在已知的 HTTP/2 协议层面故障。
3. SP3 版本（`24.03-lts-sp3`）的构建是否在同时间段内正常（可对比判断是否为 SP4 仓库专有问题）。
4. 其他 PR 中针对 SP4 的构建是否也遇到同样问题（判断是否为仓库基础设施的通病）。

## 修复验证要求
（无需验证——本次失败为 infra-error，不涉及代码修复或正则匹配上游源文件。）
