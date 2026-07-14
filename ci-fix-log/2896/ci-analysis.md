# CI 失败分析报告

## 基本信息
- PR: #2896 — chore(dotnet-deps): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 模式05
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
#8 [3/3] RUN groupadd --gid=1654 app &&     useradd -l --uid=1654 --gid=1654 --create-home app
#8 0.049 /bin/sh: line 1: groupadd: command not found
#8 ERROR: process "/bin/sh -c groupadd --gid=$APP_UID app &&     useradd -l --uid=$APP_UID --gid=$APP_UID --create-home app" did not complete successfully: exit code: 127
------
Dockerfile:21
--------------------
  20 |     
  21 | >>> RUN groupadd --gid=$APP_UID app && \
  22 | >>>     useradd -l --uid=$APP_UID --gid=$APP_UID --create-home app
  23 |     
--------------------
ERROR: failed to solve: process "/bin/sh -c groupadd --gid=$APP_UID app &&     useradd -l --uid=$APP_UID --gid=$APP_UID --create-home app" did not complete successfully: exit code: 127
```

### 根因定位
- 失败位置: `Others/dotnet-deps/8.0/24.03-lts-sp4/Dockerfile:21-22`
- 失败原因: openEuler 24.03-lts-sp4 基础镜像默认不包含 `shadow` 包（提供 `groupadd`/`useradd` 命令），Dockerfile 第 8-17 行的 `yum install` 列表遗漏了 `shadow`，导致后续第 21-22 行的 `groupadd`/`useradd` 命令找不到（exit code: 127）。

### 与 PR 变更的关联
PR 新增的 `Others/dotnet-deps/8.0/24.03-lts-sp4/Dockerfile` 直接导致了该失败。该 Dockerfile 中的 `yum install` 步骤安装了 `ca-certificates glibc libgcc libicu openssl-libs libstdc++ tzdata zlib`，但未包含 `shadow` 包。这是 openEuler 24.03 系列的已知特征（详见历史模式05），`groupadd`/`useradd` 不会预装。对比同一仓库中已有的 dotnet-deps Dockerfile（如 22.03-lts-sp3），其 `yum install` 或 `dnf install` 步骤通常已包含 `shadow`。

## 修复方向

### 方向 1（置信度: 高）
在 Dockerfile 的 `yum install` 命令中增加 `shadow` 包，使 `groupadd` 和 `useradd` 命令可用。同时建议移除 `rm -rf /var/lib/apt/lists/*`（该命令为 Debian/Ubuntu 系容器专用，在 openEuler 中无实际作用，虽然不导致构建失败，但属于错误移植），`yum clean all` 已覆盖清理逻辑。

## 需要进一步确认的点
- 可参照同仓库中已有的 `Others/dotnet-deps/8.0/22.03-lts-sp3/Dockerfile` 确认 `shadow` 包的安装方式和位置。
- README.md 和 image-info.yml 中新增条目将 `8.0-oe2403sp4` 描述为 "openEuler 22.03-LTS-SP4"，与实际镜像 `24.03-lts-sp4` 不符，建议一并修正该描述文案。

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
（不适用——此修复仅为在 `yum install` 列表中追加 `shadow` 包名，不涉及外部源文件的正则匹配。）
