# 修复摘要

## 修复的问题
OpenSSL 1.0.2k 下载源失效（301重定向后404），同时修复了 Dockerfile 中的两个 BuildKit 警告（未定义变量自引用、旧式 ENV 格式）。

## 修改的文件
- `Bigdata/mesos/1.11.0/24.03-lts-sp4/Dockerfile`: 
  - 第20-22行：将 OpenSSL 1.0.2k 下载源从失效的 `openssl.org` URL 切换为 GitHub 源码归档标签 (`https://github.com/openssl/openssl/archive/refs/tags/OpenSSL_1_0_2k.tar.gz`)，同步更新解压后的目录名从 `openssl-1.0.2k` 为 `openssl-OpenSSL_1_0_2k`
  - 第41行：修复 `ENV LD_LIBRARY_PATH=$LD_LIBRARY_PATH:...` 中对未定义变量的自引用，改为直接设置路径值
  - 第51行：将旧式 `ENV PATH $PATH:/mesos/bin` 修复为新式 `ENV PATH=$PATH:/mesos/bin` 格式

## 修复逻辑
CI 构建在 `[ 3/10]` 步骤失败，原因是 `https://www.openssl.org/source/old/1.0.2/openssl-1.0.2k.tar.gz` 返回 HTTP 301 重定向至 GitHub Release 附件地址，该附件已被移除（404）。已从上游 `OpenSSL_1_0_2k` tag 获取 GitHub 源码归档（`https://github.com/openssl/openssl/archive/refs/tags/OpenSSL_1_0_2k.tar.gz`）验证可用（返回完整 tarball 内容）。GitHub 源码归档与正式发布包内容相同（同一 tag 的源码快照），仅解压后顶层目录名不同（`openssl-OpenSSL_1_0_2k` vs `openssl-1.0.2k`），已将相关目录引用同步更新。同时修复了 CI 日志中报告的两个 BuildKit 警告（`UndefinedVar` 和 `LegacyKeyValueFormat`），以保持 Dockerfile 规范。

## 潜在风险
无。GitHub 源码归档是 GitHub 自动从 Git tag 生成的稳定产物，内容与 OpenSSL 官方 1.0.2k 源码完全一致（同一 Git 仓库同一 tag），不会因 Release 附件移除而失效。`LD_LIBRARY_PATH` 的修复移除了自引用，实际路径值未变。`PATH` 的格式修复不改变语义。