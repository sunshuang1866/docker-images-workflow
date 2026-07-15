# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库源网络波动
- 新模式症状关键词: Curl error (92), HTTP/2 stream error, INTERNAL_ERROR, Curl error (56), SSL_ERROR_SYSCALL, yum download failed, repo.openeuler.org

## 根因分析

### 直接错误
```
#7 556.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 41 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 836.2 [MIRROR] kernel-headers-6.6.0-159.4.3.154.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/kernel-headers-6.6.0-159.4.3.154.oe2403sp4.aarch64.rpm [HTTP/2 stream 59 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1029.3 [MIRROR] perl-MIME-Base64-3.16-2.oe2403sp4.aarch64.rpm: Curl error (56): Failure when receiving data from the peer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/perl-MIME-Base64-3.16-2.oe2403sp4.aarch64.rpm [OpenSSL SSL_read: SSL_ERROR_SYSCALL, errno 0]
#7 1310.2 [MIRROR] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm [HTTP/2 stream 125 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1310.2 [FAILED] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1310.3 Error: Error downloading packages:
#7 1310.3   vim-common-2:9.0.2092-36.oe2403sp4.aarch64: Cannot download, all mirrors were already tried without success
#7 ERROR: process "/bin/sh -c yum install -y         git gcc gcc-c++ make cmake which         openssl-devel         gflags-devel         protobuf-devel protobuf-compiler         abseil-cpp-devel         leveldb-devel snappy-devel &&     yum clean all && rm -rf /var/cache/yum" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4-11`（yum install 步骤）
- 失败原因: CI 在 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）上执行 `yum install` 时，从 `repo.openeuler.org` 下载多个 RPM 包（gcc、kernel-headers、perl-MIME-Base64、vim-common）均遇到 HTTP/2 流中断（`Curl error 92: INTERNAL_ERROR`）和 SSL 连接重置（`Curl error 56: SSL_ERROR_SYSCALL`），最终 `vim-common` 包因所有镜像均尝试失败而导致 yum 事务失败，整个构建中止。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了一个标准的 brpc Dockerfile 和配套元数据文件，Dockerfile 中 `yum install` 命令语法正确，依赖列表合理。失败发生在 `yum install` 从远程仓库下载 RPM 包的阶段，是 `repo.openeuler.org` 镜像站在该构建时段内的网络不稳定导致的临时性基础设施故障。同一次构建中，部分 RPM 包已成功下载（前 172/173 个包完成），仅最后 1 个包 `vim-common` 因累计网络波动无法完成。

## 修复方向

### 方向 1（置信度: 高）
**无需修改 PR 代码。** 这是 CI 基础设施网络问题，属于 `infra-error`。Code Fixer 无需处理。建议直接触发 CI 重试（re-run），待 `repo.openeuler.org` 网络恢复后构建即可通过。

### 方向 2（置信度: 低）
如果该问题反复出现，可考虑在 Dockerfile 的 `yum install` 命令前添加重试逻辑（如 `yum install -y ... || yum install -y ...`），或通过 `--setopt=retries=5` 增加 yum 内部重试次数。但鉴于 173 个包中有 172 个已成功下载，且首次出现此模式，暂不建议为此增加复杂度。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 在构建时段是否存在网络故障或维护窗口。
- 确认该 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）与其他 aarch64 runner 的网络连通性是否存在差异。
- 如果多次重试后问题仍然复现，需排查 repo.openeuler.org 的 HTTP/2 支持是否存在兼容性问题。
