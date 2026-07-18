# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
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
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（`dnf install` 步骤）
- 失败原因: CI 构建环境在通过 `dnf` 从 openEuler 24.03-LTS-SP4 软件仓库下载 RPM 包时，仓库镜像服务器反复出现 HTTP/2 流的 `INTERNAL_ERROR`（Curl error 92），多个大型包（gcc-gfortran 13MB、guile 6.3MB、gcc 34MB）下载途中被中断重试，最终 gcc 包耗尽所有重试机会，`dnf` 以 exit code 1 退出。

### 与 PR 变更的关联
与 PR 代码变更**无关**。PR 仅新增了一个合法的 multiwfn Dockerfile（基于 openEuler 24.03-LTS-SP4 基础镜像安装必要的编译依赖），Dockerfile 语法和包名均正确——日志中 `dnf` 成功解析了依赖关系（`Dependencies resolved`），所有 157 个包均存在于仓库元数据中。失败纯粹是因为 CI 构建节点与 openEuler SP4 软件仓库之间的网络链路在 HTTP/2 协议层面不稳定，导致 RPM 下载流反复被服务端 `INTERNAL_ERROR` 中断。stage-1（最终运行阶段）的 `dnf install` 也遭遇了同类下载错误（`#7 1268.5 [MIRROR] glibc-devel`、`#7 1598.9 [MIRROR] gcc-gfortran`），进一步佐证这是仓库侧问题。

## 修复方向

### 方向 1（置信度: 高）
等待 openEuler 24.03-LTS-SP4 软件仓库镜像恢复稳定后重新触发 CI。该问题为基础设施层面的临时网络/服务故障，Dockerfile 本身无需修改。可通过以下方式验证：
- 手动 `curl` 测试仓库 URL 的可达性和 HTTP/2 稳定性
- 在其他网络环境（非 CI 节点）执行相同的 `dnf install` 命令确认包可正常下载

## 需要进一步确认的点
- openEuler 24.03-LTS-SP4 仓库镜像（`repo.****.org`）在 CI 构建时段是否存在服务端 HTTP/2 协议栈故障或过载
- 同一时段其他基于 24.03-LTS-SP4 的 Dockerfile 构建是否也失败（若均失败，进一步确认是仓库全局问题；若仅此 job 失败，需排查 CI 节点到该仓库的网络路由）
