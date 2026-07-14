# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2传输错误
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
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7`（`dnf install` 步骤）
- 失败原因: CI 构建环境从 openEuler 24.03-LTS-SP4 仓库镜像下载 RPM 包时，多次遭遇 HTTP/2 流传输错误（`Curl error (92): Stream error in the HTTP/2 framing layer`），重试耗尽所有镜像后 dnf 安装失败。两个构建阶段（builder #8 和 stage-1 #7）均受波及，涉及 `gcc-gfortran`、`glibc-devel`、`guile`、`gcc` 等多个包。

### 与 PR 变更的关联
**与 PR 无关**。PR 新增的 Dockerfile 语法正确、结构合理（与同项目 sp3 版本一致），失败原因完全由 openEuler 24.03-LTS-SP4 的仓库镜像在 CI 构建期间的 HTTP/2 协议层临时故障导致，属于基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复**。该失败是 CI 基础设施/网络层问题，与 PR 代码变更无关。建议操作：**重新触发 CI 构建**（retry），等待仓库镜像恢复后构建即可通过。

### 方向 2（置信度: 低）
如果同类问题频繁出现，可在 CI 层面对 dnf 添加 HTTP/1.1 降级或增加重试次数：
- 设置 `echo "http2=false" >> /etc/dnf/dnf.conf` 禁用 HTTP/2
- 或配置 `retries=10` 增加重试次数

但这属于 CI 基础设施层面的调整，非 Dockerfile 层面的修改。

## 需要进一步确认的点
- 该 openEuler 24.03-LTS-SP4 仓库镜像（`repo.****.org`）在失败时间段是否存在已知的服务端 HTTP/2 问题，可通过 curl 手动测试确认。
- 该失败是否是同批次其他使用 sp4 的 PR 共性问题（可通过查询 CI 历史确认），若是则确认为纯粹的基础设施事件。
