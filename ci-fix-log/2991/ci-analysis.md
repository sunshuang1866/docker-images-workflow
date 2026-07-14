# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, repo.openeuler.org, INTERNAL_ERROR (err 2), dnf install

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
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`（`dnf install` 步骤）
- 失败原因: CI 在 **aarch64** runner 上执行 `dnf install` 时，`repo.openeuler.org` 的 `openEuler-24.03-LTS-SP4` 仓库在 HTTP/2 传输层出现流错误（Curl error 92: `INTERNAL_ERROR`），导致多个 RPM 包（git-core、gcc-c++、guile）下载失败。其中 guile 包重试耗尽所有镜像源后仍未成功，dnf 报错退出。

### 与 PR 变更的关联
**无关**。PR 仅新增了一个标准 Dockerfile（安装依赖 → 克隆源码 → cmake 构建 vvenc），以及对应的 README/image-info/meta.yml 条目。Dockerfile 中 `dnf install` 命令本身完全正确，失败纯粹由 `repo.openeuler.org` 仓库的 HTTP/2 服务端协议异常导致，与 PR 代码变更无关。

## 修复方向

### 方向 1（置信度: 高）
该失败为 **infra-error**，无需修改 PR 代码。应重试 CI 构建。若仓库端 HTTP/2 问题持续存在，CI 编排侧可考虑：
- 在 Dockerfile 或构建环境中配置 dnf/yum 回退到 HTTP/1.1（设置 `http2=false` 或 `proxy` 禁用 HTTP/2）
- 或使用其他 openEuler 镜像源替代默认的 `repo.openeuler.org`

### 方向 2（置信度: 低）
若 `repo.openeuler.org` 的 24.03-LTS-SP4 aarch64 仓库存在长期问题，可考虑更改基础镜像为已验证可用的版本（如 `24.03-lts-sp3`），但这不是代码缺陷所致，不推荐此方向。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 的 HTTP/2 服务器状态，该 issue 是否已修复
- 确认是否仅在 aarch64 架构 runner 上触发（x86_64 的同仓库路径是否正常）
- 该失败是否为偶发（retry CI 是否通过）
