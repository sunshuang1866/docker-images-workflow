# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2缺失
- 新模式症状关键词: shunit2, file not found, common_funs.sh, Check test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:24:00,662-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-10 09:24:00,662 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI [Check] 阶段，测试框架脚本 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh`:13
- 失败原因: CI 运行环境中缺少 `shunit2`（Shell 单元测试框架），导致容器镜像的运行时检查（Check）无法启动测试套件，直接在脚本 source 阶段失败。

### 与 PR 变更的关联
**与 PR 变更无关。** Docker 镜像的构建阶段和推送阶段均已成功完成：
- 所有 422 个编译目标均成功编译并链接（`[422/422] Linking target named`）
- `meson install` 全部安装成功（所有库文件和 man 手册均安装到位）
- Docker 构建 6 个步骤全部 DONE 且无错误
- 镜像已成功推送到 `docker.io/openeulertest/bind9:9.21.23-oe2403sp4-aarch64`
- CI 日志明确显示 `[Build] finished` 和 `[Push] finished`

失败仅发生在 eulerpublisher 测试框架的 [Check] 阶段，根因是该框架依赖的 `shunit2` 工具在 CI runner 上缺失，属于 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境中安装 `shunit2` 工具。shunit2 是一个 Shell 单元测试框架，CI 的容器检查脚本 `common_funs.sh` 需要通过 `source shunit2` 加载它来执行容器运行时测试。当前 CI runner 缺少该依赖，需要运维侧在 runner 镜像/环境中补充安装 shunit2 包。

## 需要进一步确认的点
1. 确认 amd64（x86_64）架构的构建 job 日志，判断两架构是否均成功构建、是否同样因 shunit2 缺失而失败。
2. 确认 `shunit2` 是应在 CI runner 全局安装还是通过 eulerpublisher 的依赖管理安装，以免后续其他 PR 遇到同样问题。

## 修复验证要求
无需 code-fixer 参与。此问题为 CI 基础设施依赖缺失，需运维/平台侧安装 shunit2，与 PR 代码变更无关。
