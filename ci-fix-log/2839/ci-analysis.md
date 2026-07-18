# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试框架缺失shunit2
- 新模式症状关键词: shunit2: No such file or directory, common_funs.sh, eulerpublisher, [Check] test failed

## 根因分析

### 直接错误
```
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
- 失败位置: CI Runner 环境 — `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 测试编排工具 `eulerpublisher` 的容器检查脚本 `common_funs.sh` 第 13 行尝试 `source` 加载 `shunit2` Shell 测试框架，但该框架未安装在 CI Runner 环境中，导致 `[Check]` 阶段直接失败。Docker 镜像构建和推送均已完成（`[Build] finished`、`[Push] finished`、`#11 DONE 58.0s` 推送成功），失败仅发生在 CI 自身的测试检查环节。

### 与 PR 变更的关联
**与 PR 变更无关。** 该 PR 新增了一个 postgres 17.6 在 openEuler 24.03-lts-sp4 上的 Dockerfile 及对应的 entrypoint.sh，Docker 构建和镜像推送均全部成功（`#8 DONE 268.4s` → `#11 exporting to image ... pushing layers 43.0s done`）。失败是由 CI Runner 上缺少 `shunit2` Shell 测试框架导致的，属于 CI 基础设施环境问题，非代码问题。

## 修复方向

### 方向 1（置信度: 高）
**CI 运维侧操作**：在 CI Runner 节点上安装 `shunit2` 包，确保 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh` 脚本能正确 `source` 到 `shunit2` 框架。在 openEuler 系统上可执行 `dnf install shunit2 -y` 或从 GitHub 下载安装。

### 方向 2（置信度: 低）
若确认 shunit2 已安装但路径不对，检查 CI Runner 上 `PATH` 环境变量是否包含 shunit2 所在目录，或检查 `common_funs.sh` 中 `source` 的路径是否正确。

## 需要进一步确认的点
1. CI Runner 节点上是否已安装 `shunit2` 包（`which shunit2` 或 `rpm -q shunit2`）
2. 该 CI Runner 上其他同类 PR（同 openEuler 24.03-lts-sp4 目标）的 `[Check]` 阶段是否也因相同原因失败
3. `common_funs.sh` 中第 13 行 `source` shunit2 的确切语法（是直接 `shunit2` 还是带路径的 `./lib/shunit2`），以确认安装方式
