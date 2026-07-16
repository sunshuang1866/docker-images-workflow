# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流错误
- 新模式症状关键词: `Curl error (92)`, `Stream error in the HTTP/2 framing layer`, `No more mirrors to try`, `repo.openeuler.org`

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
- 失败位置: Dockerfile:4-11（`RUN yum install -y ...` 步骤）
- 失败原因: `repo.openeuler.org` 在 aarch64 runner 上下载 `vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm` 时发生 HTTP/2 流错误（`Curl error (92): INTERNAL_ERROR`），重试耗尽所有镜像源后仍失败，导致 `yum install` 整体返回 exit code 1，Docker 构建中断。

值得注意的是，本次构建中多个包（gcc、kernel-headers、perl-MIME-Base64）先后出现了同类 HTTP/2 流错误，其中前三者在重试后均成功下载，仅 `vim-common` 在 173 个包中的最后一个耗尽重试次数。

### 与 PR 变更的关联
**与 PR 无关**。PR 仅新增了 brpc 1.16.0 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及配套元数据文件（README.md、image-info.yml、meta.yml），Dockerfile 本身的 yum 安装指令语法正确。失败完全由 `repo.openeuler.org` CDN 在 aarch64 架构上的临时性 HTTP/2 网络故障导致，属于 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
此为 openEuler 官方仓库 `repo.openeuler.org` 的临时网络/HTTP/2 协议故障，**Code Fixer 无需处理**。建议直接重新触发 CI 构建（retry），绝大多数情况下重新构建即可通过。

### 方向 2（置信度: 中）
如果该问题频繁复现（同类 Curl error 92 在同一仓库反复出现），则表明 `repo.openeuler.org` 的 HTTP/2 CDN 在 aarch64 节点上存在持续性问题。此时可考虑在 Dockerfile 的 `yum install` 前添加 `yum-config-manager --setopt=keepcache=1` 或调整 yum 的 `retries`/`timeout` 参数，但此类修改已超出 PR 变更范围，应由 CI 基础设施团队在节点环境层面统一处理。

## 需要进一步确认的点
1. 检查 `repo.openeuler.org` 在 aarch64 架构上的 HTTP/2 CDN 是否存在已知的间歇性故障（gcc、kernel-headers、perl-MIME-Base64 也出现过同类错误但在重试后恢复）。
2. 确认 `vim-common` 是否作为间接依赖被引入（PR 的 yum 安装命令中并未显式声明 vim-common，其由 git 或 gcc 等包的 `Recommends:` 依赖链自动拉入）。如果是非必要依赖，可考虑在 yum install 中添加 `--setopt=install_weak_deps=false` 跳过弱依赖以减少下载包总数，但此项改造非强制。
3. 确认该失败是否在 x86_64 runner 上也复现 — 当前日志仅记录了 aarch64 runner 的构建。
