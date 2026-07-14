# 修复摘要

## 修复的问题
Dockerfile 中硬编码的 `JDK_VERSION=11.0.30_7` 对应的 JDK 二进制包已被清华 TUNA 镜像站移除（返回 404），升级为当前镜像站可用的最新版本 `11.0.31_11`。

## 修改的文件
- `Bigdata/kyuubi/1.11.1/24.03-lts-sp4/Dockerfile`: 将 `JDK_VERSION` 从 `11.0.30_7` 更新为 `11.0.31_11`，同步更新 `JAVA_HOME` 路径。

## 修复逻辑
1. 通过 Adoptium API (`https://api.adoptium.net/v3/assets/latest/11/hotspot?image_type=jre`) 查询到 JDK 11 JRE 当前最新版本为 `11.0.31+11`（build=11），对应文件名中的版本号为 `11.0.31_11`。
2. 通过 curl HEAD 请求验证 TUNA 镜像站上 x64 和 aarch64 架构的 `OpenJDK11U-jre_{arch}_linux_hotspot_11.0.31_11.tar.gz` 文件均返回 200，确认可用。
3. 更新 `JDK_VERSION` 环境变量和 `JAVA_HOME` 路径，下载 URL（第 34 行）使用 `${JDK_VERSION}` 变量，无需额外修改。

## 潜在风险
无。该版本已通过 Adoptium API 确认同时支持 x64 和 aarch64 架构，且 TUNA 镜像站上对应文件均可用（HTTP 200）。