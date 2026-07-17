# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 软件源下载网络故障
- 新模式症状关键词: Curl error (92), Curl error (56), HTTP/2 stream, INTERNAL_ERROR, SSL_ERROR_SYSCALL, No more mirrors to try, repo.openeuler.org, yum install

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4-11`（`RUN yum install -y ...` 步骤）
- 失败原因: Docker 构建在 aarch64 runner 上执行 `yum install` 时，`repo.openeuler.org` 软件源服务器出现 HTTP/2 协议层流错误（Curl error 92）和 SSL 读取失败（Curl error 56），导致 `vim-common` RPM 包（173 个包中的最后一个）下载失败。此前 `gcc`、`kernel-headers`、`perl-MIME-Base64` 等多个包也出现过同类 MIRROR 错误但通过重试成功，最终 `vim-common` 耗尽所有重试/镜像后彻底失败。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 的 Dockerfile 内容完全正确——一个标准的 `yum install` 命令安装编译依赖，语法无任何错误。失败根因是 openEuler 官方软件源 `repo.openeuler.org` 在 CI 环境下的网络不稳定（HTTP/2 流中断、SSL 读失败），属于 CI 基础设施/上游服务端问题。同一构建中 172/173 个包均下载成功，仅最后 1 个包因累积的网络波动而耗尽重试。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建。** 该失败是 `repo.openeuler.org` 软件源的瞬时网络故障（HTTP/2 协议层错误），与 PR 代码无关。rerun CI job 大概率可以成功，因为 172/173 个包已在本次成功下载，服务器波动是暂时性的。

### 方向 2（置信度: 低）
若反复重试仍然失败，可考虑在 `yum install` 命令前添加重试或换源逻辑（如设置 `timeout=300`、`retries=10` 的 yum 配置，或使用 `repo.huaweicloud.com` 镜像源），但鉴于当前是偶发性服务端 HTTP/2 协议错误，不应优先对 Dockerfile 做修改。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 在 CI 触发时段是否存在已知的网络/服务端故障。
- 确认 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）到 `repo.openeuler.org` 的网络链路是否稳定。
