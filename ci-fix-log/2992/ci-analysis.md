# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1268.5 [MIRROR] glibc-devel-2.38-107.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer [HTTP/2 stream 17 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1598.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7`（`RUN dnf install -y git gcc gcc-c++ gcc-gfortran make openblas-devel lapack-devel && dnf clean all`）
- 失败原因: openEuler 24.03-LTS-SP4 仓库镜像服务器在通过 HTTP/2 协议传输 RPM 包时反复出现流错误（`INTERNAL_ERROR`），导致多个包（gcc-gfortran、glibc-devel、guile、gcc）下载失败，最终 `dnf` 耗尽所有镜像重试后报错退出。

### 与 PR 变更的关联
PR 变更与本次失败**无关**。PR 新增的 Dockerfile 本身结构正确——其写法与同目录下已验证通过的 `24.03-lts-sp3/Dockerfile` 模式一致，仅将基础镜像从 `24.03-lts-sp3` 升级为 `24.03-lts-sp4`。失败的根本原因是 openEuler 24.03-LTS-SP4 软件仓库的镜像服务器存在 HTTP/2 协议层面的服务端问题（服务端返回 `INTERNAL_ERROR`）。具体证据：
1. 基础镜像 `openeuler/openeuler:24.03-lts-sp4` 的 Docker 拉取**成功完成**（DONE 11.2s），说明基础镜像层不受影响。
2. 仓库元数据（`OS`、`everything`、`EPOL`、`debuginfo`、`source` 等 repo）全部成功下载，说明仓库本身可达。
3. 仅**具体 RPM 包的 HTTP/2 流传输**出现问题，且错误发生在服务端（`INTERNAL_ERROR`），非客户端网络超时或 DNS 问题。
4. 日志中 builder 阶段（#8）和 final 阶段（#7）均遭遇同样的 HTTP/2 流错误，且 builder 阶段最终因 `No more mirrors to try` 耗尽重试而失败，final 阶段被 CANCELED。

## 修复方向

### 方向 1（置信度: 中）
这是 openEuler 24.03-LTS-SP4 仓库镜像的临时性服务端问题（HTTP/2 协议流错误 `INTERNAL_ERROR`），属于基础设施故障，**非代码缺陷，Code Fixer 无需处理**。建议：
- 等待仓库镜像服务恢复后重新触发 CI 构建（retry）。
- 若持续出现相同错误，联系 openEuler 基础设施团队排查仓库镜像服务器的 HTTP/2 配置。

### 方向 2（置信度: 低）
如果仓库镜像的 HTTP/2 问题长期存在无法修复，可考虑在 Dockerfile 的 `dnf install` 命令前添加 `dnf config-manager --setopt=max_parallel_downloads=1` 降低并发度，或通过 `echo "http2=false" >> /etc/dnf/dnf.conf` 强制 dnf 回退到 HTTP/1.1 协议，以规避服务端 HTTP/2 实现缺陷。但不推荐此类 Workaround，应优先由基础设施侧修复。

## 需要进一步确认的点
1. 确认 openEuler 24.03-LTS-SP4 仓库镜像当前是否处于维护或故障状态。
2. 确认同一 CI 环境中其他使用 `24.03-lts-sp4` 基础镜像的构建 job 是否也出现相同错误——如果是，可确认为仓库侧问题。
3. 确认 aarch64 架构的构建 job 日志是否存在同样问题（当前日志仅包含 x86-64 job），以评估影响范围。

## 修复验证要求
不适用——此为 infra-error，无需代码修复。建议 CI 管理员在仓库镜像恢复后重新触发构建验证。
