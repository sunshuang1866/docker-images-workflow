# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像 HTTP/2 错误
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
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（`RUN dnf install -y git gcc gcc-c++ gcc-gfortran make openblas-devel lapack-devel && dnf clean all`）
- 失败原因: openEuler 24.03-LTS-SP4 仓库镜像在下载 RPM 包时反复出现 HTTP/2 流错误（curl error 92: `INTERNAL_ERROR`），多个包（gcc-gfortran、glibc-devel、guile、gcc）的镜像多次重试均失败，最终 gcc 包的**所有镜像均已尝试但全部失败**，dnf 无法完成安装。

### 与 PR 变更的关联

**与 PR 变更无关。** 本次 PR 新增的 Dockerfile（`Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile`）在语法和逻辑上均正确——`dnf install` 命令格式无误，所需包名均有效（日志显示 Dependencies resolved 成功，共识别 157 个待安装包）。失败发生在包下载阶段，根因是 openEuler 24.03-LTS-SP4 仓库镜像服务器的 HTTP/2 协议层内部错误（`INTERNAL_ERROR (err 2)`），属于仓库服务端的基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 重试。** 这是仓库镜像服务器的瞬时 HTTP/2 协议故障，非代码问题。等待仓库服务恢复后重新运行 CI 即可。无需修改任何代码或 Dockerfile。

## 需要进一步确认的点

- 确认 openEuler 24.03-LTS-SP4 仓库镜像当前是否正常运行（可通过浏览器或 curl 直接访问 `repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/` 验证）
- 若多次重试 CI 仍持续失败，需排查 CI runner 到仓库镜像的网络链路，确认是否存在 HTTP/2 协议协商问题或中间代理干扰
