# CI 失败分析报告

## 基本信息
- PR: #2651 — 【自动升级】ovirt-engine容器镜像升级至4.5.7版本.
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 模式09
- 新模式标题: (无)

## 根因分析

### 直接错误
```
#9 [4/5] RUN if [ "amd64" = "amd64" ]; then       BUILDARCH="x64";     elif [ "amd64" = "arm64" ]; then       BUILDARCH="aarch64";     fi     && cd /     && wget https://mirrors.tuna.tsinghua.edu.cn/Adoptium/11/jdk/amd64/linux/OpenJDK11U-jdk_amd64_linux_hotspot_11.0.27_6.tar.gz     && tar -zxvf OpenJDK11U-jdk_amd64_linux_hotspot_11.0.27_6.tar.gz     && rm -f OpenJDK11U-jdk_amd64_linux_hotspot_11.0.27_6.tar.gz
#9 0.079 --2026-06-19 00:22:25--  https://mirrors.tuna.tsinghua.edu.cn/Adoptium/11/jdk/x64/linux/OpenJDK11U-jdk_x64_linux_hotspot_11.0.27_6.tar.gz
#9 0.126 Resolving mirrors.tuna.tsinghua.edu.cn (mirrors.tuna.tsinghua.edu.cn)... 101.6.15.130, 2402:f000:1:400::2
#9 0.220 Connecting to mirrors.tuna.tsinghua.edu.cn (mirrors.tuna.tsinghua.edu.cn)|101.6.15.130|:443... connected.
#9 0.409 HTTP request sent, awaiting response... 404 Not Found
#9 0.504 2026-06-19 00:22:25 ERROR 404: Not Found.
#9 ERROR: process "/bin/sh -c ..." did not complete successfully: exit code: 8
```

### 根因定位
- 失败位置: `Cloud/ovirt-engine/4.5.7/24.03-lts-sp3/Dockerfile:18` (RUN 指令中 BUILDARCH 赋值段)
- 失败原因: `BUILDARCH` 是 BuildKit 预定义全局 ARG（值为 `amd64`/`arm64`），在 `RUN` 中对 `BUILDARCH` 重新赋值不会生效——BuildKit 会恢复内置值 `amd64`，导致下载 URL 使用了错误架构字符串 `amd64` 而非镜像站实际路径 `x64`，产生 404。

### 与 PR 变更的关联
PR 新增了 `Cloud/ovirt-engine/4.5.7/24.03-lts-sp3/Dockerfile`（全新文件），其 Dockerfile 第 18-24 行中使用了 `BUILDARCH` 变量来构造 JDK 下载 URL。该变量名与 BuildKit 预定义变量冲突，是本次失败的直接原因。

## 修复方向

### 方向 1（置信度: 高）
将 Dockerfile 中的变量名从 `BUILDARCH` 改为其他自定义名称（如 `JAVA_ARCH`、`MY_ARCH`），避免与 BuildKit 预定义变量冲突。需同时修改变量赋值语句（`if` 块内两处）和后续引用处（`wget` URL、`tar` 解压、`rm` 清理各一处）。

## 需要进一步确认的点
- 需确认 `JDK_VERSION=11.0.27_6` 在 Tsinghua Adoptium 镜像站 `x64/linux/` 路径下确实存在（修复变量名后，URL 将正确指向 `x64` 目录，若该版本在镜像站中也已下架，则还需同时处理模式03）。

## 修复验证要求
code-fixer 修复后，需验证：
1. Docker build 使用的 wget URL 是否正确拼接为 `https://mirrors.tuna.tsinghua.edu.cn/Adoptium/11/jdk/x64/linux/OpenJDK11U-jdk_x64_linux_hotspot_11.0.27_6.tar.gz`
2. 若修复变量名后仍 404，需检查 JDK 版本 `11.0.27_6` 在镜像站是否仍可用（参考模式03）
