# CI 失败分析报告

## 基本信息
- PR: #2749 — 【自动升级】guacd容器镜像升级至1.6.0版本.
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: FreeRDP开发版阻挡configure
- 新模式症状关键词: configure: error, development version of FreeRDP, --enable-allow-freerdp-snapshots, freerdp, guacamole-server

## 根因分析

### 直接错误
```
#8 11.46 checking for freerdp2 freerdp-client2 winpr2... yes
#8 11.51 checking whether FreeRDPConvertColor is declared... yes
#8 11.57 checking whether FreeRDP appears to be a development version... checking how to run the C preprocessor... gcc -E
#8 11.57 yes
#8 11.57 configure: error: 
#8 11.57   --------------------------------------------
#8 11.57    You are building against a development version of FreeRDP. Non-release
#8 11.57    versions of FreeRDP may have differences in behavior that are impossible to
#8 11.57    check for at build time. This may result in memory leaks or other strange
#8 11.57    behavior.
#8 11.57 
#8 11.57    *** PLEASE USE A RELEASED VERSION OF FREERDP IF POSSIBLE ***
#8 11.57 
#8 11.57    If you are ABSOLUTELY CERTAIN that building against this version of FreeRDP
#8 11.57    is OK, rerun configure with the --enable-allow-freerdp-snapshots
#8 11.57   --------------------------------------------
```

### 根因定位
- 失败位置: `Others/guacd/1.6.0/24.03-lts-sp3/Dockerfile:22`（`./configure --prefix="$PREFIX_DIR" $GUACAMOLE_SERVER_OPTS` 步骤）
- 失败原因: openEuler 24.03-lts-sp3 仓库中的 `freerdp` / `freerdp-devel` 包是 FreeRDP 的开发/快照版本（非正式发布版），guacamole-server 1.6.0 的 `configure` 脚本在检测到开发版 FreeRDP 后主动拒绝继续构建。

### 与 PR 变更的关联
PR 新增了 `Others/guacd/1.6.0/24.03-lts-sp3/Dockerfile`，该 Dockerfile 通过 `yum install -y ... freerdp freerdp-devel ...` 安装 FreeRDP 依赖。openEuler 24.03-lts-sp3 软件源提供的 FreeRDP 版本被 guacamole-server 的 configure 判定为开发版，导致构建中断。此失败由本次 PR 新增内容直接触发。

## 修复方向

### 方向 1（置信度: 高）
在 `./configure` 命令中添加 `--enable-allow-freerdp-snapshots` 参数，以绕过 FreeRDP 版本检查。该参数正是 configure 脚本的错误提示中明确建议的选项。

具体做法：修改 Dockerfile 中 `GUACAMOLE_SERVER_OPTS` 的默认值，在 `--disable-guaclog` 后追加 `--enable-allow-freerdp-snapshots`。

### 方向 2（置信度: 中）
尝试从 openEuler 其他软件源（如 EPOL、update 仓库）安装正式发布版的 FreeRDP 包，替换当前的开发版。但这需要确认 openEuler 24.03-lts-sp3 是否有正式发布版的 freerdp2 包可用，存在不确定性。

## 需要进一步确认的点
- 确认 openEuler 24.03-lts-sp2 的 guacd Dockerfile（`Others/guacd/1.6.0/24.03-lts-sp2/Dockerfile`）是否也遇到同一问题，以及是否已有绕过方案可参考。
- 确认 `--enable-allow-freerdp-snapshots` 对 guacd 运行时行为是否有已知副作用（如内存泄漏、协议兼容性问题）。
