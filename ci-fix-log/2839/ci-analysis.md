# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2测试框架缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, Check test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 09:40:24,021-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-09 09:40:24,021 - CRITICAL - [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh`:13
- 失败原因: CI [Check] 阶段测试框架 `shunit2`（shell 单元测试框架）未安装在 CI runner 上，导致测试脚本 `common_funs.sh` 无法加载，所有 Check 测试项均未执行（结果表格为空），`eulerpublisher` 工具判定测试失败。

### 与 PR 变更的关联
**与 PR 无关**。Docker 镜像构建阶段全部成功完成（10/10 步骤均通过，`[Build] finished`、`[Push] finished`），PostgreSQL 17.6 的编译（`make -j $(nproc) && make install`）和安装均正常，Dockerfile 和 entrypoint.sh 无问题。失败仅发生在 CI 的后置 [Check] 验证阶段，是 test runner 环境缺少 `shunit2` 导致的。

构建日志中出现的 2 个 Docker BuildKit `LegacyKeyValueFormat` 警告（ENV 写法问题）为非致命警告，不导致构建失败。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 的测试环境中安装 `shunit2` 包（如 `dnf install shunit2` 或等效方式），使 `eulerpublisher` 的 [Check] 验证阶段能正常加载测试框架并执行镜像功能测试。

### 方向 2（置信度: 低）
如果 `shunit2` 无法安装（如包仓库中没有），则需修改 `eulerpublisher` 的测试脚本 `common_funs.sh`，将 `shunit2` 改为其他可用的 shell 测试框架，或将 shunit2 作为测试依赖一并打包进 `eulerpublisher` 工具中。

## 需要进一步确认的点
- 同 CI runner 上其他镜像（如同仓库其他 PR）的 [Check] 阶段是否也因 `shunit2` 缺失而失败——若只有本 PR 失败，说明可能是本次 CI runner 实例的环境问题（如镜像/容器模板未预装 shunit2）
- `shunit2` 是否在 openEuler 的 yum 仓库中可用（包名可能为 `shunit2` 或 `shunit2-sh`）
- `eulerpublisher` 工具是否有文档说明测试阶段的依赖要求
