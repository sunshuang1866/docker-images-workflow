# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式（关联模式39"CI工具依赖缺失"）
- 新模式标题: shunit2 测试框架缺失
- 新模式症状关键词: `shunit2: No such file or directory`, `common_funs.sh`, `[Check] test failed`

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
- 失败位置: CI Runner 环境 —— `eulerpublisher` 的 Check 阶段，`/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI Runner 上缺少 `shunit2` 测试框架，`common_funs.sh` 在启动容器测试前尝试 `source` 该框架失败，导致整个 [Check] 阶段崩溃，检查结果表为空，无一检查项被执行。

### 与 PR 变更的关联
**与 PR 变更无关。** Docker 镜像构建（`make && make install`→`COPY entrypoint.sh`→`chmod`→`export&push`）全程成功完成（`#8 DONE 268.4s`, `#11 DONE 58.0s`, `[Build] finished`, `[Push] finished`）。失败仅发生在 `eulerpublisher` 的 `[Check]` 后处理阶段，原因是 CI Runner 缺少 `shunit2` 依赖，不是 PR 新增的 Dockerfile 或 entrypoint.sh 导致的。

> 注：日志中 Docker BuildKit 报告的 2 个 `LegacyKeyValueFormat` Warning（`ENV key value` 格式建议改为 `ENV key=value`）和 build tail 中出现的正常 gcc 编译命令均为非致命提示，与本次失败无关。

## 修复方向

### 方向 1（置信度: 高）
CI Runner 需要安装 `shunit2` 测试框架（可通过 `dnf install shunit2` 或等效方式安装）。这不是代码修复问题，而是 CI 基础设施配置问题。PR 作者或 CI 运维人员应在构建 runner 镜像/环境中补充 `shunit2` 包。

### 方向 2（置信度: 低，仅当方向 1 确认无效时考虑）
若安装 `shunit2` 后 [Check] 仍失败，可能的原因是该 runner 的 `eulerpublisher` 测试套件版本与当前 CI 流水线不兼容，需要更新 `eulerpublisher` 包或重新部署测试脚本。

## 需要进一步确认的点
1. 该 CI Runner 是否在同一天的其他 PR（如同类 postgres 镜像 PR）上也触发相同的 `shunit2` 缺失错误？若否，说明此 runner 环境与正常 runner 存在差异，可能需要排查 runner 节点配置漂移。
2. `shunit2` 在 openEuler 仓库中的包名是什么？（可能是 `shunit2`、`shunit` 或其他命名）需要确认正确的安装命令。
3. 如果 CI 使用容器化 runner，是否是该 runner 镜像最近更新后遗漏了 `shunit2` 依赖？
