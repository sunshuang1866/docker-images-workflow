# CI 失败分析报告

## 基本信息
- PR: #3098 — chore(impala): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 软链覆盖已存在文件
- 新模式症状关键词: ln: failed to create symbolic link, File exists, libssl

## 根因分析

### 直接错误
```
#10 50.35 ln: failed to create symbolic link '/usr/lib64/libssl.so.1.1': File exists
#10 ERROR: process "/bin/sh -c wget https://www.openssl.org/source/openssl-${OPENSSL_VERSION}.tar.gz -O /tmp/openssl-${OPENSSL_VERSION}.tar.gz &&     cd /tmp && tar -xvf openssl-${OPENSSL_VERSION}.tar.gz &&     cd openssl-${OPENSSL_VERSION} &&     ./config shared --openssldir=${OPENSSL_ROOT_DIR} --prefix=${OPENSSL_ROOT_DIR} &&     make -j$(nproc) && make install &&     ln -s ${OPENSSL_ROOT_DIR}/lib/libssl.so.1.1 /usr/lib64/libssl.so.1.1 &&     ln -s ${OPENSSL_ROOT_DIR}/lib/libcrypto.so.1.1 /usr/lib64/libcrypto.so.1.1 &&     rm -rf /tmp/*" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Bigdata/impala/4.5.0/24.03-lts-sp4/Dockerfile:28`
- 失败原因: openEuler 24.03-LTS-SP4 基础镜像已通过 `openssl-libs` RPM 包预装了 `/usr/lib64/libssl.so.1.1`，而 Dockerfile 中使用 `ln -s`（不带 `-f` 强制覆盖选项）尝试创建同名符号链接，导致命令因目标文件已存在而失败（exit code 1）。

### 与 PR 变更的关联
此次失败由 PR 新增的 Dockerfile 直接引起。第 28 行的 `ln -s` 命令未考虑基础镜像中已存在同名文件的情况，属于需修正的构建逻辑缺陷。

## 修复方向

### 方向 1（置信度: 高）
将 Dockerfile 第 28 行的 `ln -s` 改为 `ln -sf`（强制覆盖），使命令在目标已存在时先移除再创建符号链接。同时第 29 行的 `libcrypto.so.1.1` 符号链接也应同步改为 `ln -sf`，避免潜在同类问题。

### 方向 2（备选，置信度: 中）
在 `ln -s` 之前先 `rm -f /usr/lib64/libssl.so.1.1 /usr/lib64/libcrypto.so.1.1`，再创建符号链接。效果等同方向 1，但多一步操作。

## 需要进一步确认的点
- 基础镜像 `openeuler/openeuler:24.03-lts-sp4` 中 `openssl-libs` 的具体版本及提供的 `.so` 文件列表，确认是否需要覆盖系统自带的 OpenSSL 库，还是可以直接使用系统中的版本。
