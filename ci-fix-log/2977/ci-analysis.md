# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: openEuler仓库下载失败
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, repo.openeuler.org, yum install, vim-common, Cannot download, No more mirrors to try, Curl error (56), SSL_ERROR_SYSCALL

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（`RUN yum install ...` 步骤）
- 失败原因: CI 在 aarch64 runner 上执行 `yum install` 时，`repo.openeuler.org` 持续出现 HTTP/2 流错误（Curl error 92: INTERNAL_ERROR）和 SSL 读取失败（Curl error 56），导致 `vim-common` RPM 包下载失败（所有镜像源重试耗尽），构建在依赖安装阶段即终止，未进入 brpc 编译步骤。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 只新增了一个标准 Dockerfile 及配套的 README、image-info.yml、meta.yml 元数据文件，Dockerfile 中的 `yum install` 命令语法正确，包列表均属于 openEuler 24.03-LTS-SP4 仓库中的合法包。失败完全由 `repo.openeuler.org` 的 aarch64 软件源在构建期间的网络/HTTP/2 稳定性问题导致。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码，重试 CI 构建。** 这是 CI 基础设施层面的网络问题（`repo.openeuler.org` HTTP/2 流异常），PR 代码本身没有问题。等待仓库网络恢复后重新触发构建即可通过。

### 方向 2（置信度: 低）
如果 `repo.openeuler.org` 的 aarch64 仓库持续出现此类问题，可考虑在 Dockerfile 的 `yum install` 命令中添加 `--retries 10` 或 `--setopt=retries=10` 参数提高重试次数，但这属于临时规避方案，不应在正常情况下使用。

## 需要进一步确认的点
- `repo.openeuler.org` 的 aarch64 软件源在当前时间段是否有已知的网络故障或维护窗口。
- 其他 openEuler 24.03-LTS-SP4 的 PR 构建是否在同一时间段也出现了类似的 `yum install` 下载失败（若有多个案则进一步确认是仓库侧问题）。
