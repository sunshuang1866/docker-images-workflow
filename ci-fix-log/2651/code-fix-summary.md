# 修复摘要

## 修复的问题
Dockerfile 中 `BUILDARCH` 变量名与 BuildKit 预定义全局 ARG 冲突，导致 RUN 指令中对该变量的赋值被 BuildKit 覆盖，wget 下载 URL 使用了错误架构字符串 `amd64`（应为 `x64`）产生 404；同时 JDK 版本 `11.0.27_6` 在 Tsinghua Adoptium 镜像站已下架。

## 修改的文件
- `Cloud/ovirt-engine/4.5.7/24.03-lts-sp3/Dockerfile`:
  - 第 5 行：`ARG BUILDARCH` → `ARG JAVA_ARCH`
  - 第 19/21 行：RUN 内 `BUILDARCH=` 赋值 → `JAVA_ARCH=`
  - 第 24-26 行：URL/tar/rm 中的 `${BUILDARCH}` 引用 → `${JAVA_ARCH}`
  - 第 6 行：`JDK_VERSION=11.0.27_6` → `JDK_VERSION=11.0.31_11`
  - 第 28 行：`JAVA_HOME=/jdk-11.0.27+6` → `JAVA_HOME=/jdk-11.0.31+11`

## 修复逻辑
1. **BUILDARCH 冲突**（分析报告方向1）：`BUILDARCH` 是 BuildKit 预定义 ARG，在 RUN 中对其赋值不生效。重命名为 `JAVA_ARCH`（自定义名），避免冲突，使 shell 变量赋值正常生效，最终 URL 正确指向 `x64` 路径。
2. **JDK 版本下架**（分析报告「需确认」→ 模式03）：已从 Tsinghua Adoptium 镜像站 `x64/linux/` 目录验证，`11.0.27_6` 已不存在，仅有 `11.0.31_11`。同步更新 `JDK_VERSION` 和 `JAVA_HOME`（提取目录名为 `jdk-11.0.31+11`）。

## 潜在风险
无。修改仅影响 JDK 下载逻辑，`JAVA_HOME` 目录名与 tarball 解压结果一致（Adoptium 规范：`jdk-{version}+{build}`）。