# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, dnf, MIRROR, No more mirrors to try

## 根因分析

### 直接错误
```
#7 1199.1 [MIRROR] cmake-data-3.31.12-1.oe2403sp4.noarch.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/cmake-data-3.31.12-1.oe2403sp4.noarch.rpm [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1776.2 [MIRROR] git-core-2.54.0-2.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/git-core-2.54.0-2.oe2403sp4.x86_64.rpm [HTTP/2 stream 75 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1845.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 65 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 83 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [FAILED] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1970.5 Error: Error downloading packages:
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile`:6（`RUN dnf install -y ...` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 官方仓库镜像（`repo.openeuler.org`）在 CI 构建期间出现 HTTP/2 协议层流错误（`Curl error (92)`），导致 `gcc-c++` 等大包下载失败。`gcc-c++`（~13MB）在两次重试中均遇到 HTTP/2 流异常关闭（`INTERNAL_ERROR (err 2)`），DNF 耗尽所有镜像后放弃，构建失败。该错误与 PR 代码变更完全无关。

### 与 PR 变更的关联
本次 PR 仅新增了 `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile` 及配套元数据文件（README.md、image-info.yml、meta.yml）。Dockerfile 内容为标准的 `dnf install` + git clone + autoreconf + make 构建流程，所用包名和依赖清单与其他同类 Dockerfile 一致。失败发生在最基础的 `dnf install` 阶段——该步骤仅在下载 RPM 包，尚未进入任何编译环节。DNF 解析出了全部 258 个待安装包且依赖关系正确，仅因 HTTP/2 协议层错误导致部分包下载失败。因此该失败与 PR 变更**无任何关联**。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建。** 该错误为 openEuler 24.03-LTS-SP4 仓库镜像的临时性 HTTP/2 协议问题（服务端返回 `INTERNAL_ERROR`），属于基础设施层间歇性故障。同一 CI 运行中 `cmake-data` 和 `git-core` 也在首次下载时遇到同样错误，经重试后成功；仅 `gcc-c++` 两次重试均失败。重新运行 CI 后仓库镜像服务大概率恢复正常。

## 需要进一步确认的点
- 如果多次重试后仍然失败，需联系 openEuler 镜像仓库运维排查 `repo.openeuler.org` 的 HTTP/2 服务端是否有持续性问题。
- 同一 PR 在 aarch64 runner 上的构建日志（若有）可以交叉验证是否为仓库侧问题——如果 aarch64 也失败且同样是 HTTP/2 流错误，则确认为仓库基础设施问题。
