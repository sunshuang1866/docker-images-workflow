# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install, repo

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
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（`RUN dnf install` 步骤）
- 失败原因: CI 构建环境（x86_64 runner `ecs-build-docker-x86-03-sp`）从 openEuler 24.03-LTS-SP4 仓库镜像下载 RPM 包时，HTTP/2 协议层反复出现流错误（`INTERNAL_ERROR (err 2)`），多个包（gcc-gfortran、glibc-devel、guile、gcc）先后下载失败，dnd 重试耗尽所有镜像后构建终止。同时，同一构建中 `#7`（stage-1 第二个 `FROM` 阶段）也遭遇相同错误（glibc-devel、gcc-gfortran），但因 `#8` 先失败而被 `CANCELED`。

### 与 PR 变更的关联
**与 PR 变更无关。** 该 PR 仅新增了一个符合规范的 Dockerfile（模式与已有的 `24.03-lts-sp3` Dockerfile 一致），以及对应的 README、image-info.yml、meta.yml 条目。Dockerfile 语法和逻辑均正确。失败根因是 openEuler 24.03-LTS-SP4 仓库镜像的 HTTP/2 服务端存在协议层缺陷，导致 RPM 包下载在流传输过程中异常中断。

## 修复方向

### 方向 1（置信度: 高）
**等待 CI 基础设施恢复后重试。** 这是一个纯粹的 infra-error，与代码变更无关。仓库镜像的 HTTP/2 流错误属于服务端问题或 CI 网络中间设备问题，通常在服务端重启或网络抖动平息后自动恢复。Code Fixer 无需对任何文件进行修改，直接触发 re-run 即可（若重试后仍失败，需联系 CI 基础设施团队排查 openEuler 24.03-LTS-SP4 仓库 mirror 的 HTTP/2 配置）。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 仓库镜像（`repo.****.org`）在失败时段是否存在已知的服务降级或 HTTP/2 配置问题。
- 确认其他基于 `openeuler:24.03-lts-sp4` 基础镜像的新增 Dockerfile PR 是否也遇到相同错误（若是，则可确认为仓库镜像侧的普遍问题）。
- 若 re-run 后仍失败，需确认 CI runner 到仓库镜像之间的网络路径（代理、负载均衡器）是否对 HTTP/2 长连接流传输存在兼容性问题。
