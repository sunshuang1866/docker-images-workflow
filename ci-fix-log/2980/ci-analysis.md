# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 包仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install

## 根因分析

### 直接错误
```
#7 1199.1 [MIRROR] cmake-data-3.31.12-1.oe2403sp4.noarch.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/cmake-data-3.31.12-1.oe2403sp4.noarch.rpm [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]

#7 1776.2 [MIRROR] git-core-2.54.0-2.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/git-core-2.54.0-2.oe2403sp4.x86_64.rpm [HTTP/2 stream 75 was not closed cleanly: INTERNAL_ERROR (err 2)]

#7 1845.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 65 was not closed cleanly: INTERNAL_ERROR (err 2)]

#7 1970.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 83 was not closed cleanly: INTERNAL_ERROR (err 2)]

#7 1970.5 [FAILED] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success

#7 1970.5 Error: Error downloading packages:
#7 1970.5   gcc-c++-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y ...` 步骤）
- 失败原因: openEuler 24.04-LTS-SP4 官方软件包仓库在构建时段出现间歇性 HTTP/2 传输异常（Curl error 92: Stream error in the HTTP/2 framing layer），导致 `cmake-data`、`git-core`、`gcc-c++` 等多个 RPM 包下载过程中出现 HTTP/2 流未正常关闭的 `INTERNAL_ERROR`。前两个包在重试后成功下载，但 `gcc-c++` 在经历两次镜像重试后仍全部失败，dnf 耗尽所有镜像后构建终止。

### 与 PR 变更的关联
**与 PR 变更无关。** 该 PR 仅新增了 grads 2.2.3 在 openEuler 24.03-lts-sp4 上的 Dockerfile 及配套元数据文件（README.md、image-info.yml、meta.yml）。Dockerfile 中的 `dnf install` 命令语法正确、包名合理。失败完全由 openEuler 24.03-LTS-SP4 软件包仓库在 CI 构建时的网络基础设施不稳定导致，属于瞬态的 infra 故障，非代码层面问题。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复。** 失败原因为 openEuler 24.03-LTS-SP4 软件包仓库在构建时段的 HTTP/2 传输层不稳定，与 PR 提交内容无关。建议重新触发 CI 构建（retry），待仓库网络恢复后构建即可通过。

### 方向 2（置信度: 低）
如果 retry 后仍然频繁出现同类 Curl error (92)，可能是 CI runner 节点与 openEuler 仓库之间的 HTTP/2 协议兼容性问题。届时可考虑在 `dnf install` 前添加 `echo "http2=false" >> /etc/dnf/dnf.conf` 临时禁用 HTTP/2 回退到 HTTP/1.1，但不建议在正式镜像构建中保留此配置，仅作为临时诊断手段。

## 需要进一步确认的点
- 确认 retry 后 CI 能否成功通过。若 retry 通过，则确认本次为瞬态 infra 问题。
- 如果连续多次 retry 在同一仓库（repo.****.org/openEuler-24.03-LTS-SP4）出现同类 Curl error (92)，需排查该仓库的 HTTP/2 配置或 CI 网络链路。
