# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI 测试环境缺少 shunit2
- 新模式症状关键词: shunit2, file not found, common_funs.sh, Check test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:24:00,662-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-10 09:24:00,662 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`
- 失败原因: CI 测试脚本 `common_funs.sh` 第 13 行尝试通过 `. shunit2` 引入 shunit2 测试框架，但该框架在 CI runner 环境中未安装或不在 PATH 中，导致 source 命令失败，进而触发 `[Check] test failed`。

### 与 PR 变更的关联
**与 PR 无关**。此次 PR 仅新增了 bind9 在 openEuler 24.03-LTS-SP4 上的 Dockerfile、named.conf 配置文件，以及更新 README.md、meta.yml、image-info.yml 的条目。Docker 镜像构建阶段（meson 编译 422 个目标、安装、导出、推送）全部成功完成，日志中明确记录了 `[Build] finished` 和 `[Push] finished`。失败仅发生在 CI 自身的 `[Check]` 测试阶段，因 CI runner 环境缺少 `shunit2` 测试框架所致。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境中安装 `shunit2` 测试框架。`shunit2` 是一个 Shell 单元测试框架，通常可通过包管理器安装（如 `dnf install shunit2`）或从 GitHub releases 下载后放到 PATH 中。需确保 `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh` 能够成功 `. shunit2`。

### 方向 2（置信度: 低）
如果确认 shunit2 已安装但路径不在 `PATH` 中，则修改 `common_funs.sh` 第 13 行的 source 路径为 shunit2 的实际安装路径（如 `/usr/share/shunit2/shunit2`）。

## 需要进一步确认的点
1. 确认 CI runner（aarch64 架构）镜像中是否已预装 `shunit2` 包，若未安装需补充。
2. 确认 `common_funs.sh` 中引用 `shunit2` 的方式（是直接 `. shunit2` 还是依赖 `PATH`），以及 shunit2 在该 runner 上的实际安装路径。
3. 检查同类 CI check 在其他 PR 中是否也失败，若为普遍现象则确认为 CI 环境统一问题。
