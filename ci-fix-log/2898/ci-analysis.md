# CI 失败分析报告

## 基本信息
- PR: #2898 — chore(go): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式（与模式39"CI工具依赖缺失"同类，缺失组件不同）
- 新模式标题: shunit2测试框架缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, Check test failed

## 根因分析

### 直接错误
```
2026-07-09 12:32:51,073 - INFO - [Check] checking openeulertest/go:1.25.6-oe2403sp4-aarch64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 12:32:51,082-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-09 12:32:51,082 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI Host — `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 运行环境中缺少 `shunit2` 测试框架，`eulerpublisher` 的 container check 脚本（`common_funs.sh`）在第13行尝试加载 `shunit2` 时失败，导致 `[Check]` 阶段报错。

### 与 PR 变更的关联
本失败与 PR 变更**无关**。PR 仅新增了 Go 1.25.6 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及配套元数据文件（`meta.yml`、`README.md`、`image-info.yml`）。Docker 镜像构建和推送阶段（`[Build]`、`[Push]`）均成功完成，所有 Docker 构建步骤（#7-#11）均以 `DONE` 状态结束。失败仅发生在 `eulerpublisher` 工具的后置 `[Check]` 阶段，该阶段依赖的 `shunit2` 测试框架在 CI Runner 上未安装，属于 CI 基础设施环境问题。

## 修复方向

### 方向 1（置信度: 高）
在 CI Runner（`ecs-build-docker-aarch64-01-sp` 或同类 aarch64 runner）上安装 `shunit2` 包。openEuler 环境下可通过 `dnf install shunit2` 安装。此修复由 CI 运维人员执行，Code Fixer 无需对本 PR 代码做任何修改。

## 需要进一步确认的点
1. 确认该 CI Runner 上 `shunit2` 包是否可用：`dnf list shunit2` 或 `rpm -q shunit2`。
2. 确认同一个 Go 镜像在 x86_64 runner 上的 `[Check]` 阶段是否也因 `shunit2` 缺失而失败——若仅在 aarch64 runner 上缺失，说明该 runner 的测试环境部署不完整。
3. 排查是否 `shunit2` 在该 openEuler 24.03-SP4 环境的 yum 源中不可用，需换为其他安装方式（如从 GitHub Releases 下载）。
