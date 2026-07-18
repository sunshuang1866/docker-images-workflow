# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2 测试框架缺失
- 新模式症状关键词: `shunit2: file not found`, `common_funs.sh`, `check test failed`

## 根因分析

### 直接错误
```
2026-07-10 09:23:59,481 - INFO - [Build] finished
2026-07-10 09:23:59,481 - INFO - [Push] finished
2026-07-10 09:24:00,652 - INFO - [Check] checking openeulertest/bind9:9.21.23-oe2403sp4-aarch64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:24:00,662 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI Runner 上的 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 构建和推送阶段均已成功完成（`[Build] finished`、`[Push] finished`），失败发生在 `[Check]` 阶段——CI runner 上 `eulerpublisher` 测试框架的 `common_funs.sh` 脚本试图 source `shunit2` 库文件，但该文件在 CI runner 上不存在（未安装或路径配置错误）。

### 与 PR 变更的关联
**无关**。PR 仅新增了 bind9 9.21.23 在 openEuler 24.03-LTS-SP4 上的 Dockerfile（含 Dockerfile、named.conf、README.md、meta.yml、image-info.yml 的修改），Docker 镜像的构建（`meson setup` → `meson compile -j -1 -C build` → `meson install`，422 个编译目标全部成功）和推送（镜像 sha256:7a2bec1b… 推送至 `docker.io/openeulertest/bind9:9.21.23-oe2403sp4-aarch64`）均已完成。失败完全由 CI 基础设施中 `shunit2` 测试框架缺失导致，与 PR 代码变更无关。

## 修复方向

### 方向 1（置信度: 高）
在 CI Runner 上安装 `shunit2` 尚需测试框架。`shunit2` 是 shell 单元测试框架，需要被部署到 `eulerpublisher` 测试脚本所期望的路径中（即 `common_funs.sh` 中 `source` 命令能搜索到的位置）。具体操作：在 CI runner 镜像或初始化脚本中安装 `shunit2`（如通过 `dnf install shunit2` 或从 GitHub 下载后放到 `$PATH` 能搜索到的目录）。

**注意**：此问题是 CI infra-error，Code Fixer 无需对 Dockerfile 或 PR 代码做任何修改。

## 需要进一步确认的点
1. 确认 `shunit2` 在其他 CI runner（如 x86_64 架构的 runner）上是否也存在缺失问题，或者仅 aarch64 runner 有此问题。
2. 确认 `eulerpublisher` 测试框架期望 `shunit2` 安装的具体路径，以及是否可以通过环境变量（如 `SHUNIT2_HOME`）配置。
3. 如果本次 PR 仅需绑定 aarch64 架构（meta.yml 中未设置 `arch` 约束），需确认镜像在 x86_64 runner 上的 [Check] 阶段是否也会因同样原因失败。
