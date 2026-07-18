# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2 测试框架缺失
- 新模式症状关键词: shunit2: file not found, common_funs.sh, Check test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:18:18,902-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-10 09:18:18,902 - CRITICAL - [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh`:13
- 失败原因: CI 测试框架的 `common_funs.sh` 脚本在第 13 行尝试通过 `.`（source）加载 shUnit2 单元测试框架（`shunit2`），但该框架未安装于 CI runner 环境中或不在 `PATH` 内，导致 `[Check]` 阶段执行测试时立即失败。Docker 镜像构建与推送阶段均成功完成（所有 `#1~#14` 步骤均 DONE，镜像已成功推送到 registry）。

### 与 PR 变更的关联
与 PR 变更无关。本次 PR 新增了 httpd 2.4.66 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及配套文件（`httpd-foreground` 脚本、README.md、image-info.yml、meta.yml 更新），Docker 构建过程成功完成（编译、安装、配置、镜像导出推送全部通过），失败发生在 CI 平台的 `eulerpublisher` 测试框架调用 `shunit2` 时——这是 CI 环境自身问题，非 PR 代码引起。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 上安装 `shunit2` 测试框架。shUnit2 是一个 POSIX shell 单元测试库，通常可通过以下方式之一获取：
- `dnf install shunit2`（如果 openEuler 仓库提供了该包）
- 从 GitHub 下载并置于 CI 测试脚本可发现的位置（`PATH` 或 `common_funs.sh` 期望的目录）

## 需要进一步确认的点
- 确认 CI runner 节点上是否已安装 `shunit2`，如果已安装但路径不对，检查 `common_funs.sh` 第 13 行 source 的路径是否与实际 `shunit2` 安装位置一致
- 排查是否为特定 CI runner 节点（而非所有节点）缺失该依赖，以及是否仅有本次运行的节点受影响
- 检查其他成功通过 Check 阶段的同类镜像（如 httpd 2.4.66-oe2403sp2）的 CI job 日志，确认同一 runner 上是否也曾调用 `shunit2` 但当时该框架存在
