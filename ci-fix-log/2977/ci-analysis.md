# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: openEuler仓库HTTP/2中断
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, repo.openeuler.org, yum install, aarch64

## 根因分析

### 直接错误
```
#7 1310.2 [MIRROR] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm [HTTP/2 stream 125 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1310.2 [FAILED] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1310.3 Error: Error downloading packages:
#7 1310.3   vim-common-2:9.0.2092-36.oe2403sp4.aarch64: Cannot download, all mirrors were already tried without success
#7 ERROR: process "/bin/sh -c yum install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（`yum install` 步骤）
- 失败原因: 在 aarch64 构建节点上，`yum install` 从 `repo.openeuler.org` 下载 `vim-common` RPM 包时遭遇 HTTP/2 帧流传输错误（curl error 92），重试所有镜像后仍失败。整个下载阶段（约 21 分钟）内共出现 4 次类似 curl 错误（gcc、kernel-headers、perl-MIME-Base64 各一次，均重试成功；vim-common 重试失败导致最终构建中断）。

### 与 PR 变更的关联
与 PR 变更**无关**。该 PR 仅新增了一个标准的 brpc 编译 Dockerfile，`yum install` 步骤中的依赖列表（git、gcc、gcc-c++、cmake、openssl-devel、gflags-devel、protobuf-devel、protobuf-compiler、abseil-cpp-devel、leveldb-devel、snappy-devel）均为 openEuler 24.03-LTS-SP4 仓库中正常存在的包，失败纯因下载 `vim-common`（作为 git 的间接依赖被拉入）时 `repo.openeuler.org` 镜像站 HTTP/2 连接不稳定。

## 修复方向

### 方向 1（置信度: 高）
本失败为 CI 基础设施网络问题（HTTP/2 流错误），与代码变更无关。建议直接重新触发 CI 构建，无需修改任何文件。若重试仍失败，可在 Dockerfile 的 `yum install` 命令中增加 `--setopt=retries=10` 增大下载重试次数以增加对间歇性网络波动的容错能力。

## 需要进一步确认的点
无。日志证据充分，失败原因为 `repo.openeuler.org` 镜像站 HTTP/2 传输中断。
