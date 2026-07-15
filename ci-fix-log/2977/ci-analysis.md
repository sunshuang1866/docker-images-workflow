# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 软件源下载网络故障
- 新模式症状关键词: Curl error, Stream error in the HTTP/2 framing layer, No more mirrors to try, yum, repo.openeuler.org, aarch64

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
#7 ERROR: process "/bin/sh -c yum install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（`yum install` 步骤）
- 失败原因: CI 构建过程中，openEuler 官方软件源 `repo.openeuler.org` 出现 HTTP/2 流传输中断（`INTERNAL_ERROR`）和 SSL 连接异常（`SSL_ERROR_SYSCALL`），导致多个 aarch64 RPM 包（gcc、kernel-headers、perl-MIME-Base64、vim-common）下载失败。最终 `vim-common` 包在所有重试后仍无法下载，yum 安装流程终止。

### 与 PR 变更的关联
**与 PR 无关。** 本次 PR 仅新增了一个标准格式的 `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile` 及配套元数据文件（README.md、image-info.yml、meta.yml）。Dockerfile 中的 `yum install` 命令语法正确，所需软件包均为 openEuler 24.03-LTS-SP4 仓库中的标准包。失败完全是由 CI 运行期间 `repo.openeuler.org` 软件源的网络故障引起的，属于短暂的、与代码无关的基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
**触发 CI 重试（re-run）。** 此失败是 `repo.openeuler.org` 软件源临时的 HTTP/2 网络故障，PR 代码本身无任何问题。重新触发 CI job 后，若软件源恢复，构建即可通过。Code Fixer 无需对任何文件做修改。

## 需要进一步确认的点
- 若多次重试后仍持续失败，需要确认 `repo.openeuler.org` 的 aarch64 仓库是否存在持续性的服务端 HTTP/2 配置问题或 CDN 节点故障。可联系 openEuler 基础设施团队排查 `repo.openeuler.org` 的 HTTP/2 服务端日志。
