# 修复摘要

## 修复的问题
Dockerfile 中 `BUILDARCH` 变量名与 BuildKit 预定义全局 ARG 冲突，导致下载 URL 中架构字符串错误（`amd64` 而非 `x64`），且 JDK 版本 `11.0.27_6` 在清华镜像站已不可用，共同导致 404 构建失败。

## 修改的文件
- `Cloud/ovirt-engine/4.5.7/24.03-lts-sp3/Dockerfile`:
  1. 删除 `ARG BUILDARCH`（与 BuildKit 预定义变量冲突，且在 RUN 中重赋值无效）
  2. 将 RUN 块内的 shell 变量 `BUILDARCH` 重命名为 `JDK_ARCH`（共 7 处）
  3. 将 `JDK_VERSION` 从 `11.0.27_6` 升级为 `11.0.31_11`
  4. 将 `JAVA_HOME` 从 `/jdk-11.0.27+6` 更新为 `/jdk-11.0.31+11`

## 修复逻辑

**根因 1（BuildKit 变量冲突）**：`BUILDARCH` 是 BuildKit 预定义的全局 ARG，值为 `amd64` 或 `arm64`。在 `RUN` 指令中对其赋值 `BUILDARCH="x64"` 不会生效（BuildKit 会恢复为内置值），导致 wget URL 使用 `amd64` 而非 `x64`，产生 404。修复方案：移除全局 `ARG BUILDARCH` 声明，改用不与 BuildKit 冲突的自定义 shell 变量 `JDK_ARCH`。

**根因 2（JDK 版本不可用）**：已从清华镜像站 `https://mirrors.tuna.tsinghua.edu.cn/Adoptium/11/jdk/x64/linux/` 和 `.../aarch64/linux/` 验证，`11.0.27_6` 已下架，唯一可用版本为 `11.0.31_11`。同步更新 `JDK_VERSION` 和 `JAVA_HOME` 以匹配。

## 潜在风险
无。仅修改变量名和镜像站中确认存在的版本号，不影响其他功能。