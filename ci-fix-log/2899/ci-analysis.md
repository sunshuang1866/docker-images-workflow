# CI 失败分析报告

## 基本信息
- PR: #2899 — chore(guacd): add openEuler 24.03-LTS-SP4 support
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: FreeRDP快照检测阻断
- 新模式症状关键词: `configure: error: You are building against a development version of FreeRDP`, `--enable-allow-freerdp-snapshots`, `guacamole-server`

## 根因分析

### 直接错误
```
#8 6.999 checking for freerdp2 freerdp-client2 winpr2... yes
#8 7.006 checking whether FreeRDPConvertColor is declared... yes
#8 7.033 checking whether FreeRDP appears to be a development version... checking how to run the C preprocessor... gcc -E
#8 7.072 yes
#8 7.072 configure: error:
#8 7.072   --------------------------------------------
#8 7.072    You are building against a development version of FreeRDP. Non-release
#8 7.072    versions of FreeRDP may have differences in behavior that are impossible to
#8 7.072    check for at build time. This may result in memory leaks or other strange
#8 7.072    behavior.
#8 7.072
#8 7.072    *** PLEASE USE A RELEASED VERSION OF FREERDP IF POSSIBLE ***
#8 7.072
#8 7.072    If you are ABSOLUTELY CERTAIN that building against this version of FreeRDP
#8 7.072    is OK, rerun configure with the --enable-allow-freerdp-snapshots
#8 7.072   --------------------------------------------
```

### 根因定位
- 失败位置: `Others/guacd/1.6.0/24.03-lts-sp4/Dockerfile:22-26`（`./configure` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的软件源中 `freerdp`/`freerdp-devel` 包为开发版/快照版本（非稳定发布版），guacamole-server 的 `configure` 脚本内置了对开发版 FreeRDP 的检测与阻断逻辑，检测到开发版本后直接退出，拒绝继续编译。

### 与 PR 变更的关联
PR 新增了 `Others/guacd/1.6.0/24.03-lts-sp4/Dockerfile`，该 Dockerfile 通过 `yum install -y ... freerdp freerdp-devel ...` 安装了 openEuler 24.03-LTS-SP4 仓库中的 FreeRDP 包。这些包被 guacamole-server 的 configure 脚本判定为开发版本，导致构建失败。该问题由 PR 引入的新 Dockerfile 直接触发，与代码逻辑无关，属于平台软件包版本兼容性问题。

## 修复方向

### 方向 1（置信度: 高）
在 `GUACAMOLE_SERVER_OPTS` 变量或 `./configure` 命令中追加 `--enable-allow-freerdp-snapshots` 标志，显式声明允许 guacamole-server 链接开发版 FreeRDP。该标志正是 configure 脚本错误信息中建议的绕过方案，且来自 guacamole-server 官方构建系统的内置开关，最为安全直接。修改位置：Dockerfile 第 5 行的 `ARG GUACAMOLE_SERVER_OPTS` 默认值，在 `--disable-guaclog` 后追加 `--enable-allow-freerdp-snapshots`。

### 方向 2（置信度: 低）
尝试在 openEuler 24.03-LTS-SP4 中寻找并安装 FreeRDP 的稳定发布版 RPM 包（非 freerdp-devel 开发分支构建）。但 openEuler 官方仓库很可能只提供这一版本，且自行构建或引入第三方 RPM 会增加维护复杂度和安全风险，不推荐。

## 需要进一步确认的点
- openEuler 24.03-LTS-SP4 仓库中是否确实只有开发版 FreeRDP 包而无稳定发布版可用（需登录对应节点或查阅仓库元数据确认）
- 同一镜像在 24.03-LTS-SP2（已有的 `1.6.0-oe2403sp2`）上是否存在同样问题，以判断这是 SP4 特有的软件包版本问题还是所有 openEuler 版本的共性问题

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
不涉及正则 patch 外部源文件，无需此步骤。
