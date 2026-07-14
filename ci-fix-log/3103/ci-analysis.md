# CI 失败分析报告

## 基本信息
- PR: #3103 — chore(kyuubi): add openEuler 24.03-LTS-SP4 support
- 失败类型: dependency-error
- 置信度: 高
- 知识库匹配: 模式03
- 新模式标题: (不适用)
- 新模式烟雾关键词: (不适用)

## 根因分析

### 直接错误
```
#10 [builder 5/5] RUN if [ "amd64" = "amd64" ]; then BUILDARCH="x64"; ...
#10 0.061 --2026-07-10 05:10:31--  https://mirrors.tuna.tsinghua.edu.cn/Adoptium/11/jre/x64/linux/OpenJDK11U-jre_x64_linux_hotspot_11.0.30_7.tar.gz
#10 0.091 Resolving mirrors.tuna.tsinghua.edu.cn (mirrors.tuna.tsinghua.edu.cn)... 101.6.15.130, 2402:f000:1:400::2
#10 0.092 Connecting to mirrors.tuna.tsinghua.edu.cn|101.6.15.130|:443... connected.
#10 0.364 HTTP request sent, awaiting response... 404 Not Found
#10 0.464 2026-07-10 05:10:31 ERROR 404: Not Found.
#10 ERROR: process "/bin/sh -c ..." did not complete successfully: exit code: 8
ERROR: failed to solve: ...
```

### 根因定位
- 失败位置: `Bigdata/kyuubi/1.11.1/24.03-lts-sp4/Dockerfile:28-36`（JDK 下载 RUN 指令块）
- 失败原因: Dockerfile 中硬编码的 `JDK_VERSION=11.0.30_7` 对应的 JDK 二进制包已被清华 TUNA 镜像站移除（Adoptium 镜像站仅保留最新 build，旧 build 覆盖后返回 404）

### 与 PR 变更的关联
- **直接关联**。本次 PR 新增的 Dockerfile `Bigdata/kyuubi/1.11.1/24.03-lts-sp4/Dockerfile` 直接硬编码了 `JDK_VERSION=11.0.30_7`。
- 该版本号与 kyuubi SP3 版本 Dockerfile（`1.11.1/24.03-lts-sp3/Dockerfile`）中使用的 JDK 版本相同，该版本曾在 PR #2105 中作为修复从 `11.0.28_6` 升级而来。但 `11.0.30_7` 现已同样被镜像站轮转下线。
- 其他文件（README.md、image-info.yml、meta.yml）的改动均为文档和元数据更新，与构建失败无关。

### 次要发现
- Docker BuildKit 输出一条风格警告（非错误）：`FromAsCasing: 'as' and 'FROM' keywords' casing do not match (line 3)`，即第 3 行 `FROM ${BASE} as builder` 中 `as` 使用了小写。不影响构建结果，仅风格问题。

## 修复方向

### 方向 1（置信度: 高）
将 `ENV JDK_VERSION=11.0.30_7` 升级为镜像站当前可用的最新 JDK 11 build 号。需先确认 `https://mirrors.tuna.tsinghua.edu.cn/Adoptium/11/jre/x64/linux/` 目录下当前托管的最新版本文件名，取对应的完整 build 号（如 `11.0.XX_Y`）更新 `JDK_VERSION` 环境变量。

## 需要进一步确认的点
- 需确认 TUNA 镜像站上 Adoptium JDK 11 当前可用的最新 build 号。可以通过访问 `https://mirrors.tuna.tsinghua.edu.cn/Adoptium/11/jre/x64/linux/` 目录列表获取实际文件名。
- 需确认 arm64（aarch64）架构下对应的 JDK 二进制包同样存在于镜像站。

## 修复验证要求
- code-fixer 在修改 `JDK_VERSION` 前，必须访问 `https://mirrors.tuna.tsinghua.edu.cn/Adoptium/11/jre/x64/linux/` 和 `https://mirrors.tuna.tsinghua.edu.cn/Adoptium/11/jre/aarch64/linux/` 确认目标版本的 `OpenJDK11U-jre_{arch}_linux_hotspot_{version}.tar.gz` 文件实际存在，然后再更新 Dockerfile 中的 `JDK_VERSION` 值。
