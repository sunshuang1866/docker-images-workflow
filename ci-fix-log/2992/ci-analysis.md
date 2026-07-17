# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流中断
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, No more mirrors to try, dnf install

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
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（`dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 官方 RPM 仓库（`repo.****.org`）在 CI 构建期间反复出现 HTTP/2 协议层流错误（`Curl error (92): Stream error in the HTTP/2 framing layer`），导致多个 RPM 包（`gcc-gfortran`、`glibc-devel`、`guile`、`gcc` 等）下载失败。其中 `gcc-12.3.1-110.oe2403sp4.x86_64.rpm` 在多次重试后所有镜像均不可用，`dnf install` 最终以退出码 1 失败。

### 与 PR 变更的关联
**与 PR 无关**。PR 变更仅为：
1. 新增 `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile`（与已有 sp3 版本结构完全一致，仅基础镜像改为 24.03-lts-sp4）
2. 更新 `meta.yml`、`image-info.yml`、`README.md` 以注册新镜像

Dockerfile 本身语法和依赖声明正确，构建失败完全由 openEuler 包仓库的网络层面 HTTP/2 协议异常导致，属于 CI 基础设施问题。

另外值得注意的是，同一构建中的 stage-1（`#7`）也遭遇了相同仓库的 HTTP/2 流错误（`glibc-devel`、`gcc-gfortran` 下载出现同样的 `Curl error (92)`），说明问题出在仓库服务端而非某一特定阶段。

## 修复方向

### 方向 1（置信度: 高）
此为 openEuler 官方 RPM 仓库的临时性网络/服务端问题，**无需对 PR 代码做任何修改**。建议直接重试 CI 构建（re-trigger），在仓库恢复后构建应能正常通过。

### 方向 2（置信度: 中）
如果该仓库持续不稳定，可在 Dockerfile 的 `dnf install` 命令中增加 `--retries` 参数或配置 DNS/HTTP/1.1 回退，但这属于 CI 环境的配置调整而非 Dockerfile 层面的修复。

## 需要进一步确认的点
- 确认 `repo.****.org`（openEuler 24.03-LTS-SP4 仓库）当前服务状态是否正常
- 确认 CI 构建节点到该仓库的网络连通性及 HTTP/2 协议兼容性
- 可对比同仓库其他 24.03-lts-sp4 镜像的 CI 构建状态，判断是否为大面积基础设施故障
