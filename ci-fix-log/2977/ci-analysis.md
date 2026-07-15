# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像站HTTP/2协议错误
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, repo.openeuler.org, yum install, Error downloading packages

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
- 失败位置: Dockerfile:4-11（`yum install` 步骤）
- 失败原因: CI 构建节点在 aarch64 架构上下载 `vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm` 时，`repo.openeuler.org` 镜像站返回 HTTP/2 协议层错误（`INTERNAL_ERROR (err 2)`），多次重试后仍失败，导致 yum 事务中断。

### 补充观察
同一构建过程中，多个其他 RPM 包也曾遇到 HTTP/2 错误但重试成功（如 `gcc-12.3.1-110` 在第 556 秒、`kernel-headers-6.6.0` 在第 836 秒、`perl-MIME-Base64` 在第 1029 秒遇到 curl error 56），说明 `repo.openeuler.org` 在该时间段存在网络不稳定问题。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了 `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile` 以及配套的 README、image-info.yml、meta.yml 元数据文件。失败发生在新 Dockerfile 的 `yum install` 阶段，该阶段仅从 openEuler 官方软件源下载系统包，Dockerfile 写法与同类镜像一致，无语法错误。失败根因为 `repo.openeuler.org` 镜像站在该时间段出现 HTTP/2 传输错误，属于 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码。** 这是 `repo.openeuler.org` 镜像站的瞬时网络故障。建议重新触发 CI 运行（retry），待镜像站恢复后构建应能通过。

### 方向 2（置信度: 中）
如果重试多次仍持续失败，可考虑在 `yum install` 前添加 `yum-config-manager` 调低 yum 的 curl 超时或禁用 HTTP/2 回退至 HTTP/1.1（如设置 `http2=0` 或调整 yum 重试参数 `retries=10`），但这是 workaround 而非根因修复，且当前 Dockerfile 无需此类修改。

## 需要进一步确认的点
- 确认 `repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/` 目录下 `vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm` 文件是否真实存在且文件大小完整。
- 确认 CI 构建节点的出网网络到 `repo.openeuler.org` 的 HTTP/2 连接是否持续不稳定。

## 修复验证要求
不涉及代码修复，无需验证步骤。若需验证是否为瞬时故障，重新触发 CI 构建即可。
