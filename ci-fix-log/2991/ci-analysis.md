# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, dnf install, repo.openeuler.org, No more mirrors to try

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
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`
- 失败原因: `dnf install` 从 `repo.openeuler.org` 下载多个 RPM 包（git-core、gcc-c++、guile）时遭遇 HTTP/2 流错误（Curl error 92: `HTTP/2 stream was not closed cleanly: INTERNAL_ERROR`），`guile` 包所有镜像重试均失败，导致 dnf 安装步骤整体失败。此为 openEuler 官方仓库的 HTTP/2 协议层间歇性问题，与 PR 代码变更无关。

### 与 PR 变更的关联
PR 变更仅新增了一个标准的 Dockerfile（安装编译依赖后构建 vvenc），以及配套的 README.md、meta.yml、image-info.yml 更新。Dockerfile 中的 `dnf install -y git gcc gcc-c++ make cmake && dnf clean all` 命令语法完全正确，无任何逻辑问题。失败纯粹由 openEuler 仓库 `repo.openeuler.org` 的 HTTP/2 传输层间歇性错误导致，**与 PR 改动无关**。这是基础设施层面的瞬时网络故障。

## 修复方向

### 方向 1（置信度: 中）
由于此失败为 infra-error（openEuler 仓库 HTTP/2 协议层抖动），通常无需修改任何代码。建议触发 CI 重试（re-run），在仓库网络恢复正常的时段重新构建。

### 方向 2（置信度: 低）
如果该仓库的 HTTP/2 问题频繁出现，可考虑在 Dockerfile 的 `dnf install` 前添加 `echo 'http1_only=True' >> /etc/dnf/dnf.conf` 来强制 dnf 使用 HTTP/1.1，规避 HTTP/2 流错误。但考虑到这只是瞬时基础设施问题（该仓库通常是可用的），不建议为此修改代码。

## 需要进一步确认的点
1. 检查同一时间段内其他 PR 在 aarch64 上是否也出现了类似的 `Curl error (92)` 报错——若有，可确认是仓库侧问题
2. 确认 x86_64 架构的构建是否也失败——当前日志仅包含 aarch64 构建的日志
3. 重试构建后是否成功——如果重试成功，则证实为瞬时网络问题
