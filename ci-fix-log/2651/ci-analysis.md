# CI 失败分析报告

## 基本信息
- PR: #2651 — 【自动升级】ovirt-engine容器镜像升级至4.5.7版本.
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 模式09
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
#9 0.805 2026-06-19 04:03:08 ERROR 404: Not Found.
#9 ERROR: process "/bin/sh -c if [ \"$TARGETARCH\" = \"amd64\" ]; then       BUILDARCH=\"x64\";     elif [ \"$TARGETARCH\" = \"arm64\" ]; then       BUILDARCH=\"aarch64\";     fi     && cd /     && wget https://mirrors.tuna.tsinghua.edu.cn/Adoptium/11/jdk/${BUILDARCH}/linux/OpenJDK11U-jdk_${BUILDARCH}_linux_hotspot_${JDK_VERSION}.tar.gz     && tar -zxvf OpenJDK11U-jdk_${BUILDARCH}_linux_hotspot_${JDK_VERSION}.tar.gz     && rm -f OpenJDK11U-jdk_${BUILDARCH}_linux_hotspot_${JDK_VERSION}.tar.gz" did not complete successfully: exit code: 8
```

日志中实际解析出的 URL 为：
```
https://mirrors.tuna.tsinghua.edu.cn/Adoptium/11/jdk/amd64/linux/OpenJDK11U-jdk_amd64_linux_hotspot_11.0.27_6.tar.gz
```
正确 URL 应为 `x64` 而非 `amd64`：
```
https://mirrors.tuna.tsinghua.edu.cn/Adoptium/11/jdk/x64/linux/OpenJDK11U-jdk_x64_linux_hotspot_11.0.27_6.tar.gz
```

### 根因定位
- 失败位置: `Cloud/ovirt-engine/4.5.7/24.03-lts-sp3/Dockerfile`:21
- 失败原因: Dockerfile 在 `RUN` 指令中使用 `BUILDARCH` 作为变量名，并尝试赋值为 `x64`，但 `BUILDARCH` 是 BuildKit 的预定义全局 ARG（固定值为 `amd64`/`arm64`），在 `RUN` 中对其重新赋值不会生效——BuildKit 恢复为内置值 `amd64`，导致 wget 用错误架构字符串构造下载 URL，产生 404。

### 与 PR 变更的关联
本次 PR 新增了完整的 `Cloud/ovirt-engine/4.5.7/24.03-lts-sp3/Dockerfile`，其中第 21-29 行的 `RUN` 指令使用了 `BUILDARCH` 变量名。该变量名与 BuildKit 预定义变量冲突，是导致此次 CI 失败的直接原因。非 PR 无关的预存问题。

## 修复方向

### 方向 1（置信度: 高）
将 Dockerfile 中 `BUILDARCH` 变量名改为不与 BuildKit 预定义变量冲突的自定义名称（如 `JAVA_ARCH`、`MY_ARCH`），同时更新所有引用该变量的位置（`wget` URL、`tar` 和 `rm` 命令）。

```
ARG BUILDARCH → ARG JAVA_ARCH
BUILDARCH="x64" → JAVA_ARCH="x64"
```

## 需要进一步确认的点
- 变量重命名后，需确认 JDK 版本 `11.0.27_6` 在清华镜像站 `https://mirrors.tuna.tsinghua.edu.cn/Adoptium/11/jdk/x64/linux/` 目录下确实存在（当前因 URL 路径错误无法判断版本是否可用；若版本也不可用，则需同时升级 `JDK_VERSION`，参考模式03）。
- arm64 架构下，确认清华镜像站对应路径 `https://mirrors.tuna.tsinghua.edu.cn/Adoptium/11/jdk/aarch64/linux/` 中 `11.0.27_6` 版本也存在。

## 修复验证要求
code-fixer 在提交前，必须验证 `https://mirrors.tuna.tsinghua.edu.cn/Adoptium/11/jdk/x64/linux/` 目录下实际存在 `OpenJDK11U-jdk_x64_linux_hotspot_11.0.27_6.tar.gz`，以及 aarch64 对应路径下也存在同名文件（架构字符串为 aarch64）。如果版本 `11.0.27_6` 在镜像站已下架，需同步升级 `JDK_VERSION` 到当前镜像站可用版本。
