# CI 失败分析报告

## 基本信息
- PR: #3144 — chore(text-embeddings-inference-cpu): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: Intel 仓库证书不受信
- 新模式症状关键词: `apt.repos.intel.com`, `certificate is NOT trusted`, `Certificate verification failed`, `gpg: no valid OpenPGP data found`, `cargo-chef`, `bookworm`

## 根因分析

### 直接错误
```
#13 0.491 ERROR: The certificate of 'apt.repos.intel.com' is not trusted.
#13 0.491 ERROR: The certificate of 'apt.repos.intel.com' doesn't have a known issuer.
#13 0.491 gpg: no valid OpenPGP data found.
#14 8.136 Err:7 https://apt.repos.intel.com/oneapi all InRelease
#14 8.136   Certificate verification failed: The certificate is NOT trusted. The certificate issuer is unknown.  Could not handshake: Error in the certificate verification. [IP: 23.50.17.186 443]
#14 8.476 W: Failed to fetch https://apt.repos.intel.com/oneapi/dists/all/InRelease  Certificate verification failed: The certificate is NOT trusted. The certificate issuer is unknown.
#14 8.893 E: Unable to locate package intel-oneapi-mkl-devel
> [builder  2/10] RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends     intel-oneapi-mkl-devel=2024.0.0-49656     build-essential     && rm -rf /var/lib/apt/lists/*:
------
ERROR: failed to solve: process "/bin/sh -c apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends     intel-oneapi-mkl-devel=2024.0.0-49656     build-essential     && rm -rf /var/lib/apt/lists/*" did not complete successfully: exit code: 100
```

### 根因定位
- 失败位置: `AI/text-embeddings-inference-cpu/1.7.0/24.03-lts-sp4/Dockerfile:43-46`（builder 阶段的 `apt-get install` 步骤）
- 失败原因: `builder` 阶段基于 `lukemathwalker/cargo-chef:latest-rust-1.85-bookworm`（Debian Bookworm）镜像。该基础镜像的 CA 证书信任链不包含 Intel 软件仓库 CDN（`apt.repos.intel.com`，实际由 Akamai CDN 提供服务）的 TLS 证书颁发机构，导致 wget 无法下载 GPG 公钥，apt 也无法从 Intel 仓库获取 `intel-oneapi-mkl-devel` 包。注意：同一构建中 Debian 官方仓库（`deb.debian.org`）的 HTTPS 访问正常，说明问题仅限 Intel CDN 的证书链。

### 与 PR 变更的关联
**直接关联**。PR 新增的 Dockerfile 在多阶段构建中定义了一个基于 Debian Bookworm（cargo-chef）的 `builder` 阶段，该阶段需要通过 Intel apt 仓库安装 `intel-oneapi-mkl-devel`。Intel CDN（由 Akamai 提供服务）使用的 TLS 证书链在 cargo-chef/Bookworm 基础镜像的 CA 信任库中不被识别，导致构建失败。该文件为新增文件，失败由该文件的引入直接触发。

## 修复方向

### 方向 1（置信度: 高）
在 builder 阶段访问 Intel 仓库之前，先安装/更新 `ca-certificates` 包并刷新证书信任库：
- 在 `wget` 和 `apt-get update` 之前添加 `RUN apt-get update && apt-get install -y ca-certificates && update-ca-certificates`
- 或者：在 `wget` 命令中添加 `--no-check-certificate`，并在 apt sources.list 中使用 `[trusted=yes]` 标记 Intel 仓库为受信（降低安全性，不推荐）
- 或者：检查 Intel 是否提供 HTTP（非 HTTPS）的 apt 仓库地址作为替代

### 方向 2（置信度: 中）
如果 cargo-chef 镜像默认不含完整的 CA 证书包，改用基于 `openeuler/openeuler:24.03-lts-sp4` 的 builder（但 Rust 工具链安装会变得复杂），或换用其他包含更新 CA 证书的 Debian 基础镜像作为 builder 阶段基底。

## 需要进一步确认的点
1. `lukemathwalker/cargo-chef:latest-rust-1.85-bookworm` 镜像是否已包含 `ca-certificates` 包，还是需要手动安装
2. Intel CDN（`apt.repos.intel.com` / Akamai IP `23.50.17.186`）的 TLS 证书是否近期有过变更，导致 Bookworm 默认 CA 库不识别
3. 是否存在其他已成功构建的同仓库 Dockerfile（使用非 Bookworm 基础镜像访问 Intel 仓库）可作为参考

## 修复验证要求
- code-fixer 在提交前，应验证 cargo-chef 镜像中 `ca-certificates` 的安装情况和 `update-ca-certificates` 的执行效果
- 若采用方向 1，需确认 `apt-get install ca-certificates` 在前置步骤执行后，后续 `wget` 和 `apt-get update` 能成功访问 `apt.repos.intel.com`
