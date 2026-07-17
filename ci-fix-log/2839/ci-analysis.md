# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2 测试框架缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, Check test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 09:40:24,021-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-09 09:40:24,021 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI [Check] 阶段引用的测试框架 `shunit2` 在运行环境中不存在，`common_funs.sh` 第 13 行尝试 source/调用 `shunit2` 时失败。Docker 镜像构建和推送均已成功完成（`#8 DONE 268.4s`、`#11 DONE 58.0s`，日志明确显示 `[Build] finished` 和 `[Push] finished`），失败仅发生在构建后的容器功能检查阶段。

### 与 PR 变更的关联
与本次 PR 的代码变更**完全无关**。PR 仅新增了 PostgreSQL 17.6 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 和 entrypoint.sh，Docker 构建和推送环节全部成功。`shunit2: No such file or directory` 是 CI Runner 上 `eulerpublisher` 测试框架自身的环境问题，不是 Dockerfile 或构建逻辑导致的。

## 修复方向

### 方向 1（置信度: 高）
确认 `eulerpublisher` 测试框架所依赖的 `shunit2` 安装路径是否存在于执行 [Check] 的 CI Runner 上。若缺失，需由 CI 管理员在 Runner 镜像中安装 `shunit2` 或将 `shunit2` 脚本部署到 `common_funs.sh` 期望的路径下。此问题非代码层面可修复，Code Fixer 无需操作。

## 需要进一步确认的点
1. `common_funs.sh` 中第 13 行对 `shunit2` 的引用方式（是绝对路径、相对路径，还是 `PATH` 查找），以确定安装的目标位置。
2. 该 CI Runner 上是否其他应用镜像（Database 或其他类别）的 [Check] 阶段也因同样原因失败，还是仅此 Runner 环境有异常。
3. `shunit2` 是否曾经被部署过但因 Runner 镜像更新而丢失。
