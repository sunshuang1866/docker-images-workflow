# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: Yum仓库网络不稳定
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, Curl error (56), SSL_ERROR_SYSCALL, No more mirrors to try, repo.openeuler.org

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（`RUN yum install` 步骤，Docker build 第 `[2/6]` 层）
- 失败原因: CI 在 aarch64 节点（`ecs-build-docker-aarch64-04-sp`）上执行 `yum install` 时，`repo.openeuler.org` 仓库持续出现 HTTP/2 流错误（curl error 92）和 SSL 读取错误（curl error 56），多个包（gcc、kernel-headers、perl-MIME-Base64）经重试后恢复下载，但最后一个包 `vim-common`（173 个包中的第 173 个）重试耗尽后下载失败，导致整个 yum 事务回滚。

### 与 PR 变更的关联
与 PR 变更**无关**。PR 仅新增了一个语法正确的 Dockerfile 及配套元数据文件更新。Dockerfile 中 `yum install` 的包名（git、gcc、gcc-c++、make、cmake、which、openssl-devel、gflags-devel、protobuf-devel、protobuf-compiler、abseil-cpp-devel、leveldb-devel、snappy-devel）均存在且正确，失败纯粹由 `repo.openeuler.org` 仓库在构建期间（2026-07-09 13:45 UTC）网络不稳定导致。

日志中的错误链证据：
1. `#7 556.2` — gcc 下载首次 HTTP/2 流错误 → 重试后于 `#7 831.9` 成功
2. `#7 836.2` — kernel-headers 下载 HTTP/2 流错误 → 重试后于 `#7 855.7` 成功
3. `#7 1029.3` — perl-MIME-Base64 下载 SSL 错误 → 重试后于 `#7 1030.5` 成功
4. `#7 1310.2` — vim-common（第 173/173 个包）HTTP/2 流错误 → 重试耗尽，致命失败

连续 4 次网络错误说明 openEuler 仓库在 aarch64 包分发节点上存在持续性的 HTTP/2 协议栈或 CDN 问题，与 Dockerfile 内容无关。

## 修复方向

### 方向 1（置信度: 中）
重试 CI 构建。由于这是 `repo.openeuler.org` aarch64 仓库的网络临时故障，Dockerfile 本身无需修改。等待仓库网络恢复后重新触发 CI 构建，本次失败应不再复现。

### 方向 2（置信度: 低）
若网络问题持续，可考虑在 Dockerfile 的 `yum install` 之前添加 `yum makecache` 或为 `yum` 配置更长的重试参数（如 `--retries 10 --timeout 300`），但此方向仅作为防御性措施，不解决根因。

## 需要进一步确认的点
1. `repo.openeuler.org` 的 openEuler-24.03-LTS-SP4 aarch64 仓库在 2026-07-09 13:45 UTC 前后是否存在已知的网络故障或维护窗口。
2. 同一时间段内其他 PR 的 aarch64 构建是否也出现类似 yum 下载失败（可确认是否为系统性网络问题）。
3. 该 PR 的 x86_64 构建 job 是否成功（若能获取 x86_64 日志，可进一步确认问题仅限 aarch64 仓库节点）。
