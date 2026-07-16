# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库下载网络故障
- 新模式症状关键词: Curl error (92), Curl error (56), HTTP/2 framing layer, stream error, No more mirrors to try, repo.openeuler.org

## 根因分析

### 直接错误
```
#7 1310.2 [MIRROR] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm [HTTP/2 stream 125 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1310.2 [FAILED] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1310.3 Error: Error downloading packages:
#7 1310.3   vim-common-2:9.0.2092-36.oe2403sp4.aarch64: Cannot download, all mirrors were already tried without success
#7 ERROR: process "/bin/sh -c yum install -y         git gcc gcc-c++ make cmake which         openssl-devel         gflags-devel         protobuf-devel protobuf-compiler         abseil-cpp-devel         leveldb-devel snappy-devel &&     yum clean all && rm -rf /var/cache/yum" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（`RUN yum install ...` 步骤）
- 失败原因: aarch64 构建节点在从 `repo.openeuler.org` 下载 `vim-common` RPM 包时，HTTP/2 连接发生流错误（INTERNAL_ERROR），yum 耗尽所有镜像重试后仍下载失败。构建过程中另有 3 个包（gcc、kernel-headers、perl-MIME-Base64）也出现同类 Curl 网络错误但重试成功。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 本次 PR 新增的 `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile` 语法正确，`yum install` 包列表中的所有依赖均被仓库识别（日志中 "Dependencies resolved" 和 173 个包的 Transaction Summary 均正常），失败纯粹由 `repo.openeuler.org` 在 aarch64 架构上的网络波动导致 `vim-common` 包下载失败。

## 修复方向

### 方向 1（置信度: 高）
重新触发 CI 构建。这是 openEuler 官方仓库 `repo.openeuler.org` 在 aarch64 构建时刻的网络瞬时故障（HTTP/2 流错误），与 PR 的 Dockerfile 内容无关。同类包（gcc、kernel-headers、perl-MIME-Base64）在重试后均下载成功，仅 `vim-common` 碰巧在重试耗尽前未能在短暂的网络恢复窗口内完成下载。重新跑一次构建即可通过。

## 需要进一步确认的点
- 无需进一步确认。日志中 yum 的 Transaction Summary 显示所有 173 个包均被仓库识别和定位，Dockerfile 中指定的包名正确，故障本质为网络瞬时问题。

## 修复验证要求
无需验证。本失败为 infra-error，不涉及代码修复或正则 patch。
