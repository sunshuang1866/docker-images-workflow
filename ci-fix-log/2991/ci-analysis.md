# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: openEuler仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, repo.openeuler.org, aarch64

## 根因分析

### 直接错误
```
#7 1273.6 [MIRROR] git-core-2.54.0-2.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/git-core-2.54.0-2.oe2403sp4.aarch64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1419.8 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 39 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1548.4 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 51 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [MIRROR] guile-2.2.7-6.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/guile-2.2.7-6.oe2403sp4.aarch64.rpm [HTTP/2 stream 49 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [FAILED] guile-2.2.7-6.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1709.7 Error: Error downloading packages:
#7 ERROR: process "/bin/sh -c dnf install -y git gcc gcc-c++ make cmake && dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y git gcc gcc-c++ make cmake && dnf clean all`）
- 失败原因: CI aarch64 构建节点在通过 `dnf install` 从 `repo.openeuler.org` 下载 openEuler-24.03-LTS-SP4 的 aarch64 架构 RPM 包时，多个包（git-core、gcc-c++、guile）遭遇 HTTP/2 流错误（Curl error 92: Stream error in the HTTP/2 framing layer, INTERNAL_ERROR）。其中 git-core 和 gcc-c++ 经重试后下载成功，但 guile 包所有重试均耗尽（"No more mirrors to try"），最终导致 dnf 退出码 1，Docker 镜像构建失败。

### 与 PR 变更的关联
**与 PR 变更无关**。本次 PR 仅新增了 `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile` 及配套元数据文件（README.md、image-info.yml、meta.yml），Dockerfile 中的 `dnf install` 命令语法完全正确（与仓库中其他 openEuler 24.03-lts-sp4 下的 Dockerfile 写法一致）。失败由 `repo.openeuler.org` 镜像站在 aarch64 架构上的 HTTP/2 传输层间歇性问题触发，属于 CI 基础设施故障。

## 修复方向

### 方向 1（置信度: 高）
**等待基础设施恢复后重试。** 该失败是 `repo.openeuler.org` 对 aarch64 包的 HTTP/2 传输间歇性故障。Code Fixer 无需修改任何代码。建议：
- 确认 `repo.openeuler.org` 的 openEuler-24.03-LTS-SP4 aarch64 仓库状态正常后，重新触发 CI 构建。
- 如果该问题频繁出现，可考虑在 Dockerfile 的 `dnf install` 命令中增加 `--setopt=retries=10` 提高重试次数，或临时为 dnf 配置使用 HTTP/1.1 协议禁用 HTTP/2 以规避服务端 HTTP/2 实现缺陷。

## 需要进一步确认的点
1. 确认 `repo.openeuler.org` 的 openEuler-24.03-LTS-SP4 aarch64 仓库是否存在已知的 HTTP/2 服务端问题（可通过在浏览器或 curl 中直接下载 guile 包测试确认）。
2. 若该问题为偶发，重跑 CI 即可通过；若持续失败，需调查是否是 openEuler 24.03-LTS-SP4 aarch64 仓库镜像基础设施存在持续性问题。
