# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, repo.openeuler.org

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4-11`（`yum install` 步骤）
- 失败原因: CI 在 aarch64 节点（`ecs-build-docker-aarch64-04-sp`）上构建时，从 `repo.openeuler.org` 下载 `vim-common` 包（7.8 MB）过程中遭遇 HTTP/2 流错误（Curl error 92: Stream error in the HTTP/2 framing layer），dnf 镜像重试机制耗尽所有重试后仍无法成功下载。在整个 yum 安装过程中，先后有 `gcc`（30 MB）、`kernel-headers`（1.7 MB）、`perl-MIME-Base64`（19 kB）三个包也出现了同类 HTTP/2 流错误，但均通过 dnf 的重试机制恢复成功；`vim-common` 是第四个受影响且唯一一个重试耗尽后失败的包。

### 与 PR 变更的关联
**PR 变更与失败无关。** PR 仅新增了一个标准的 brpc Dockerfile（包含常规的 `yum install` 构建依赖命令），同时更新了 README.md、image-info.yml 和 meta.yml 三个元数据文件。失败发生在 `yum install` 下载 `vim-common` 这一传递依赖（由 `vim-enhanced` → `gcc-c++`/`git` 的依赖链引入）时，根本原因是 `repo.openeuler.org` 的 openEuler 24.03-LTS-SP4 aarch64 仓库在下载部分 RPM 包时存在 HTTP/2 协议层面的不稳定问题。Dockerfile 本身没有错误。

## 修复方向

### 方向 1（置信度: 高）
**重试构建即可**。此为 `repo.openeuler.org` 仓库服务器的 HTTP/2 协议间歇性不稳定导致的临时性网络错误，与代码无关。Code Fixer 无需修改任何文件。建议等待仓库服务恢复后触发重新构建，或在 CI pipeline 中为重试失败的 `yum install` 步骤增加重试逻辑（如 `yum install --retries 5` 或在 RUN 命令前包裹 retry wrapper）。

### 方向 2（置信度: 低）
若重试多次均失败，可能是 SP4 aarch64 仓库中 `vim-common-9.0.2092-36` 包本身存在文件损坏问题。可联系 openEuler 镜像站维护团队确认该包在仓库侧的完整性。

## 需要进一步确认的点
- `repo.openeuler.org` 的 openEuler-24.03-LTS-SP4 aarch64 仓库在构建时刻是否存在服务端 HTTP/2 实现缺陷或网络拥堵。由于多个不同大小的包均出现同类错误（gcc 30MB、kernel-headers 1.7MB、perl-MIME-Base64 19kB、vim-common 7.8MB），表明这是仓库服务端的普遍性 HTTP/2 协议不稳定问题，而非特定文件损坏。
- 如果多个不相关的 PR 在同一时段对 SP4 aarch64 构建均失败，可进一步确认为仓库侧问题。

## 修复验证要求
无需修复。如决定重试构建，仅需在 CI 中重新触发即可。
