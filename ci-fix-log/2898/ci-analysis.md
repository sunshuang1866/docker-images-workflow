# CI 失败分析报告

## 基本信息
- PR: #2898 — chore(go): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 模式39（CI工具依赖缺失）
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
2026-07-09 12:32:51,073 - INFO - [Check] checking openeulertest/go:1.25.6-oe2403sp4-aarch64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 12:32:51,082 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI 编排工具 `eulerpublisher` 的 [Check] 阶段，文件 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI Runner 上的测试脚本 `common_funs.sh` 尝试 source 加载 `shunit2` 测试框架，但该框架未安装在 CI Runner 环境中（`No such file or directory`），导致容器镜像的 post-build 测试检查阶段失败。

### 与 PR 变更的关联
**与 PR 变更无关**。证据如下：
1. Docker 镜像构建和推送均成功完成：日志中 `#11 DONE 41.9s`、"`[Build] finished`"、"`[Push] finished`" 表明 Dockerfile 本身的构建逻辑无任何错误。
2. 失败仅发生在构建后的 [Check] 测试阶段，错误为 CI Runner 自身缺少 `shunit2` 测试框架，属于 CI 基础设施环境问题。
3. PR 变更仅涉及新增 1 个 Dockerfile（Go 1.25.6 on 24.03-LTS-SP4）及 3 个元数据文件（README.md、image-info.yml、meta.yml），所有构建步骤（yum 安装依赖、下载解压 go 二进制包、文件时间戳修正、构建工具卸载）均在日志中正常完成，无报错。

## 修复方向

### 方向 1（置信度: 高）
CI Runner 环境缺少 `shunit2` 测试框架。需由 CI 基础设施维护者在 Runner 上安装 `shunit2`（如通过 `dnf install shunit2` 或将 shunit2 脚本部署到 `/usr/local/etc/eulerpublisher/tests/` 路径下），使其可被 `common_funs.sh` source 加载。

## 需要进一步确认的点
- 确认 CI Runner（`ecs-build-docker-aarch64-01-sp` 或同类节点）上 `shunit2` 是否曾正常安装、是否被意外移除或版本升级导致路径变更。
- 确认同一 CI 环境中其他 PR 的 [Check] 阶段是否也出现相同 `shunit2` 缺失错误（若普遍存在，则确认为 Runner 级别问题）。
