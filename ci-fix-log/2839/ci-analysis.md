# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试框架缺失shunit2
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, check test failed

## 根因分析

### 直接错误
```
[Build] finished
[Push] finished
[Check] checking ****test/postgres:17.6-oe2403sp4-x86_64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 09:40:24,021 - CRITICAL - [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`（CI 测试框架内部文件）
- 失败原因: CI Runner 上缺少 `shunit2` Shell 测试框架，`common_funs.sh` 在第 13 行尝试 source/执行 `shunit2` 时找不到该文件，导致整个 Check 阶段崩溃。Docker 镜像构建（Build）和推送（Push）均成功完成，失败仅发生在测试/检查阶段。

### 与 PR 变更的关联
**与 PR 变更无关。** 此次 PR 仅新增了 PostgreSQL 17.6 在 openEuler 24.03-LTS-SP4 上的 Dockerfile、entrypoint.sh、meta.yml 条目和 README 表格行。Docker 镜像构建和推送均已成功（日志中 `#8 DONE 268.4s`、`[Build] finished`、`[Push] finished` 及 image manifest push 均正常），表明新增的 Dockerfile 和 entrypoint.sh 在编译和打包层面没有问题。失败纯粹发生在 CI 框架的 Check 阶段，由 Runner 环境缺少 `shunit2` 依赖导致。

## 修复方向

### 方向 1（置信度: 高）
CI Runner 环境缺少 `shunit2` Shell 测试框架。需在 CI Runner 上安装 `shunit2`（通常通过包管理器安装或从 GitHub releases 下载），确保 `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh` 能正常加载 `shunit2`。这不是 PR 代码层面的问题，Code Fixer 无需修改任何 PR 文件。

### 方向 2（置信度: 低）
若确认 CI Runner 上实际已安装 `shunit2`，则可能为 `common_funs.sh` 中 `shunit2` 的引用路径不正确。需要检查 `common_funs.sh` 第 13 行的具体写法（是 `source shunit2`、`. shunit2` 还是带绝对路径），确认 `shunit2` 是否在 `PATH` 中或需要调整路径引用。

## 需要进一步确认的点
1. 该 CI Runner 上是否曾经成功执行过 Check 阶段的 `shunit2` 测试？若之前其他镜像的 Check 均成功，则本次可能是 Runner 环境变更（如重新部署）导致 `shunit2` 丢失。
2. `common_funs.sh` 第 13 行引用 `shunit2` 的具体方式（绝对路径 vs 相对路径 vs PATH 查找），以判断是缺少安装还是路径配置问题。
3. 同一 CI 流水线中其他镜像（如同批次的其他 PR）的 Check 阶段是否也因同样原因失败，以确认是全局环境问题还是此 Runner 个例。
