# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 包仓库HTTP/2流错误
- 新模式症状关键词: `Curl error (92)`, `Stream error in the HTTP/2 framing layer`, `INTERNAL_ERROR`, `No more mirrors to try`, `repo.****.org`

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-9`（dnf install 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 软件包仓库镜像（`repo.****.org`）在处理 HTTP/2 请求时持续返回 `INTERNAL_ERROR`（Curl error 92），导致 `dnf` 下载 `gcc`、`gcc-gfortran`、`guile`、`glibc-devel` 等多个 RPM 包失败，最终因所有镜像均已尝试但均未成功而构建终止。运行时阶段（#7 stage-1）同样遭遇相同 HTTP/2 流错误，但被取消。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 本次 PR 仅新增了一个基于 `openeuler:24.03-lts-sp4` 基础镜像的 Dockerfile 及配套文档/元数据文件。Dockerfile 中的 `dnf install` 命令写法与同仓库其他 Dockerfile（如同目录下 sp3 版本）完全一致。失败根源是 openEuler 24.03-LTS-SP4 软件包仓库服务器端在处理 HTTP/2 请求时出现的流错误，属于 CI 环境与上游仓库之间的网络/基础设施问题。

已有的 `cb37c53-oe2403sp3` 镜像使用 openEuler 24.03-LTS-SP3 软件源，并未出现此类问题，进一步说明这是 SP4 仓库侧的孤立问题，与 Dockerfile 本身无关。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建。** 此类 HTTP/2 Stream Error (INTERNAL_ERROR) 通常为仓库镜像服务器的**瞬时性网络问题**，可能与 CDN 节点的 HTTP/2 连接处理不稳定有关。等待仓库恢复后重试构建（retrigger）即可通过。

### 方向 2（置信度: 低）
**若问题持续存在**，可能是 openEuler 24.03-LTS-SP4 仓库的特定镜像节点存在持久性 HTTP/2 实现缺陷。此时需联系仓库运维排查服务端 HTTP/2 配置，或在 Dockerfile 构建前添加 `dnf config-manager` 配置临时切换到其他可用镜像源。

## 需要进一步确认的点

1. 重试 CI 后是否仍然出现相同的 HTTP/2 错误——若多次重试均失败，则可能是 openEuler 24.03-LTS-SP4 仓库的持久性问题而非瞬时故障。
2. 其他使用 `openeuler:24.03-lts-sp4` 基础镜像的 Dockerfile（如 `Others/` 下其他已存在的 sp4 版本）是否也同时失败——如果是，则证实为仓库侧全局问题。
3. CI runner 与 `repo.****.org` 之间的网络链路是否正常（是否存在代理或防火墙干扰 HTTP/2 长连接）。
