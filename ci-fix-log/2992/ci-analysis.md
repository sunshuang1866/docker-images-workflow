# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流中断
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]

#7 1268.5 [MIRROR] glibc-devel-2.38-107.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/glibc-devel-2.38-107.oe2403sp4.x86_64.rpm [HTTP/2 stream 17 was not closed cleanly: INTERNAL_ERROR (err 2)]

#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]

#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（`dnf install` 阶段，builder 镜像）
- 失败原因: openEuler 24.03-LTS-SP4 的 RPM 仓库镜像（`repo.****.org`）在下载 `gcc`、`gcc-gfortran`、`glibc-devel`、`guile` 等多个较大 RPM 包时，HTTP/2 连接发生流中断（`INTERNAL_ERROR (err 2)`），curl 反复重试所有可用镜像均失败，最终 dnf 无法完成包下载而退出。

### 与 PR 变更的关联
**与 PR 代码改动无关。** PR 仅新增了 multiwfn 在 openEuler 24.03-LTS-SP4 上的 Dockerfile、更新了 README/image-info.yml/meta.yml 等元数据文件，Dockerfile 语法和内容均正确。失败发生在 `dnf install` 从外部仓库下载 RPM 包阶段，属于 CI 构建环境的网络基础设施故障——openEuler 24.03-LTS-SP4 镜像仓库在该时段 HTTP/2 服务不稳定。值得注意的是，同一个 CI 构建中的 stage-1 镜像（`#7`）在下载同样来自 SP4 仓库的包时也遇到了相同的 HTTP/2 流错误（`glibc-devel`、`gcc-gfortran`），只是 builder 镜像（`#8`）的包更多、下载量更大，先达到致命失败点。

## 修复方向

### 方向 1（置信度: 高）
**无需修改任何代码。** 这是 CI 基础设施的网络问题，属于 transient 故障。Code Fixer 无需对 PR 代码做任何改动，应由 CI 维护者确认 openEuler 24.03-LTS-SP4 镜像仓库的 HTTP/2 服务状态后重新触发构建即可。

### 方向 2（置信度: 低，仅当方向1反复失败时考虑）
如果反复重试后该镜像仓库持续出现 HTTP/2 流中断错误，可以考虑在 Dockerfile 中 `dnf install` 之前将 dnf 配置为使用 HTTP/1.1 协议（如 `echo "http2=false" >> /etc/dnf/dnf.conf` 或设置 curl 选项），绕过 HTTP/2 协议的流中断问题。但此为 infra 层面的绕过方案，不建议在代码中永久保留。

## 需要进一步确认的点
- openEuler 24.03-LTS-SP4 镜像仓库（`repo.****.org`）的 HTTP/2 服务在故障发生时段的可用性状态。
- 其他同样使用 openEuler 24.03-LTS-SP4 基础镜像的 PR 是否也在同一时段遇到了同样的 HTTP/2 流中断错误，以排除 PR 专属因素。
