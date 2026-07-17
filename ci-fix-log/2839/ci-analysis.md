# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: shunit2测试框架缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, Check test failed

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
- 失败位置: CI Runner 上的 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 测试框架 `eulerpublisher` 的公共函数脚本 `common_funs.sh` 在第 13 行尝试引用 `shunit2`（Shell 单元测试框架），但 `shunit2` 未安装在当前 CI runner 上，导致 Check 阶段所有测试无法加载执行，检查结果表为空，CI 判定构建失败。

### 与 PR 变更的关联
**与 PR 无关。** PR 的变更（新增 PostgreSQL 17.6 on openEuler 24.03-LTS-SP4 的 Dockerfile、entrypoint.sh、meta.yml 条目、README 更新）均与 Docker 构建阶段相关。Docker 镜像构建和推送已完全成功：

- `./configure && make -j "$(nproc)" && make install` 全部通过（`#8 DONE 268.4s`）
- 镜像导出、推送均成功（`#11 DONE 58.0s`）
- CI 日志明确记录 `[Build] finished` 和 `[Push] finished`

失败发生在构建/推送之后的 `[Check]` 阶段，是 CI runner 测试环境缺少 `shunit2` 依赖所致，属于基础设施问题，与 PR 的 Dockerfile、entrypoint.sh 或其他代码变更无关。

## 修复方向

### 方向 1（置信度: 中）
在 CI runner 上安装 `shunit2` 测试框架。`shunit2` 是一个 Shell 单元测试框架，常见安装方式为通过包管理器（如 `apt install shunit2`、`dnf install shunit2`）或从 GitHub 下载（`https://github.com/kward/shunit2`）。确认安装后，`common_funs.sh` 第 13 行的引用应能正常解析。

### 方向 2（置信度: 低）
若其他并行构建的同类型镜像（如 postgres 17.6 on sp2）的 Check 阶段正常通过，则可能是该 CI runner 的部署配置遗漏了 `shunit2`。此时需要在 CI 编排配置中确保 `shunit2` 作为前置依赖安装。

## 需要进一步确认的点
1. `common_funs.sh` 第 13 行的具体内容是什么（是 `source shunit2`、`. shunit2`，还是其他形式的引用），以确认 `shunit2` 的预期安装路径。
2. 该 CI runner 上其他 Database 类镜像（如同仓库中已存在的 postgres 17.6-oe2403sp2）的 Check 阶段是否也因同样原因失败，还是一直能通过。如果是后者，说明该 runner 最近发生了变更导致了 `shunit2` 丢失。
3. `shunit2` 是否作为 `eulerpublisher` 的依赖项在 CI runner 初始化脚本中安装，还是需要单独配置。
4. Dockerfile 中两个 ENV 格式警告（`LegacyKeyValueFormat` at lines 26, 30）虽不导致失败，但建议一并修正为 `ENV key=value` 格式以消除警告。
