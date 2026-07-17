# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR (err 2), No more mirrors to try, dnf install

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
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7`
- 失败原因: openEuler 24.03-LTS-SP4 的 RPM 仓库镜像在通过 HTTP/2 协议传输大型软件包（gcc、gcc-gfortran、guile 等）时反复出现 HTTP/2 流层 `INTERNAL_ERROR`（Curl error 92），导致 DNF 重试所有镜像后仍无法下载 `gcc-12.3.1-110.oe2403sp4.x86_64.rpm`（34 MB），构建失败。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 这是 openEuler 24.03-LTS-SP4 仓库镜像的基础设施问题。

日志中两个 Docker 构建阶段（`#7` stage-1 和 `#8` builder）均从同一组仓库镜像下载 RPM 包，且都遭遇了 `Curl error (92): Stream error in the HTTP/2 framing layer`：

- `#7`（stage-1，仅需 32 个包）：`glibc-devel` 和 `gcc-gfortran` 下载时出现同样的 HTTP/2 流错误，但因包数量少、部分通过重试恢复，最终被 `#8` 的失败触发 `CANCELED`
- `#8`（builder，需 157 个包）：`gcc-gfortran`、`guile`、`gcc` 三个大型包均出现 HTTP/2 流错误，`gcc` 在耗尽所有镜像重试后仍下载失败

PR 新增的 Dockerfile 语法和使用方式均正确，与历史 `cb37c53-oe2403sp3` 版本的 Dockerfile 模式一致。问题出在 openEuler 仓库镜像侧。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修改，重新触发 CI 构建即可。** 该失败是 openEuler 24.03-LTS-SP4 RPM 仓库镜像的临时网络/协议故障（HTTP/2 流层 `INTERNAL_ERROR`），属于基础设施层面的间歇性问题。在仓库镜像恢复后重新运行 CI 有很大概率通过。

### 方向 2（置信度: 低）
如果多次重试仍持续失败，可能是 openEuler 24.03-LTS-SP4 仓库的特定镜像节点存在 HTTP/2 协议实现问题。此时需联系 openEuler 基础设施团队排查仓库镜像的 HTTP/2 服务配置，或在 Dockerfile 中为 DNF 配置 `http2=0` 降级为 HTTP/1.1 协议进行安装（`echo "http2=0" >> /etc/dnf/dnf.conf`）。

## 需要进一步确认的点
1. 重新触发 CI 后是否仍然失败——以排除临时性网络波动。
2. 如果持续失败，需确认 openEuler 24.03-LTS-SP4 仓库镜像的 HTTP/2 服务状态是否正常。
3. 检查其他使用 openEuler 24.03-lts-sp4 基础镜像的 CI 构建（如同期其他 PR）是否也出现了同样的 HTTP/2 流错误——若普遍存在则可确认是仓库基础设施问题。
