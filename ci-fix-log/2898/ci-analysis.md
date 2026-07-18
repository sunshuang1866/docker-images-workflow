# CI 失败分析报告

## 基本信息
- PR: #2898 — chore(go): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2 测试依赖缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, Check test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 12:32:51,082 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI Runner 上 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 后置检查阶段（[Check]）中，测试框架脚本 `common_funs.sh` 尝试通过 `source` 或命令执行方式引用 `shunit2`，但该 Shell 测试库未安装在 CI runner 环境中，导致检查步骤直接失败。

### 与 PR 变更的关联
**与 PR 变更无关。** 本次 PR 的改动为纯增量操作——新增 Go 1.25.6 在 openEuler 24.03-LTS-SP4 上的 Dockerfile（34行新文件）、在 README.md 和 image-info.yml 中追加版本条目、在 meta.yml 中注册新镜像路径。Docker 镜像的构建和推送均已完成且成功（日志 #7~#11 显示构建、导出、推送全部通过，`[Build] finished` 和 `[Push] finished` 均正常输出）。失败发生在构建/推送之后的容器镜像健康检查阶段（`[Check]`），原因是 CI 编排工具 `eulerpublisher` 的测试环境缺少 `shunit2` 依赖，与本次新增的 Go Dockerfile 及元数据文件无关。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 镜像或构建环境中安装 `shunit2` 测试框架。openEuler 系统上可通过以下方式安装：
- `dnf install shunit2`（若 openEuler 仓库提供该包）
- 或从 `https://github.com/kward/shunit2` 下载并将其脚本路径加入 `PATH`

此修复需由 CI 基础设施维护团队在 runner 环境层面执行，不涉及本次 PR 的任何代码或 Dockerfile 修改。

## 需要进一步确认的点
- CI runner 列表是否统一安装了 `shunit2`，还是仅特定标签/架构的 runner 缺失该依赖。
- 本次 aarch64 runner 上 `shunit2` 缺失是否为近期 CI 环境变更导致（对比同仓库其他近期成功构建的 [Check] 通过记录）。
- amd64 架构的同版本构建 job 是否也因同样原因失败（日志中仅可见 aarch64 构建，需确认 amd64 job 的完整日志）。

## 修复验证要求
无需代码修复。确认 CI runner `shunit2` 安装完毕后，重新触发 PR #2898 的 CI 流水线，观察所有架构（amd64, arm64）的 [Check] 阶段是否通过即可。
