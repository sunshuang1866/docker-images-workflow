# 修复摘要

## 修复的问题
openEuler 24.03-LTS-SP4 基础镜像已预装 `libssl.so.1.1`，Dockerfile 中 `ln -s` 创建符号链接时因目标文件已存在而失败。

## 修改的文件
- `Bigdata/impala/4.5.0/24.03-lts-sp4/Dockerfile`: 将第 28、29 行的 `ln -s` 改为 `ln -sf`（强制覆盖符号链接）

## 修复逻辑
CI 分析报告指出，基础镜像 `openeuler/openeuler:24.03-lts-sp4` 通过 `openssl-libs` RPM 包预装了 `/usr/lib64/libssl.so.1.1`，而 Dockerfile 构建过程中又编译安装了自定义版本的 OpenSSL 并尝试创建同名符号链接。`ln -s` 在目标已存在时会报 `File exists` 错误并返回 exit code 1，导致整个 RUN 命令失败。

将 `ln -s` 改为 `ln -sf`（`-f` 强制覆盖），使命令在目标文件已存在时先移除再创建，不会因文件已存在而失败。同时将 `libcrypto.so.1.1` 的符号链接也同步修改，避免同类问题。

## 潜在风险
无。`ln -sf` 仅当目标存在时才执行移除+创建，行为与先 `rm -f` 再 `ln -s` 等价，不会引入额外副作用。