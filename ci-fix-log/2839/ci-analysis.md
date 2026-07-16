# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试框架缺失shunit2
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, [Check] test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 09:40:24,021-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: CI runner 测试环境（`/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`）
- 失败原因: CI [Check] 阶段使用的测试脚本 `common_funs.sh` 第 13 行尝试加载 `shunit2`（Shell 单元测试框架），但该工具未安装在 CI runner 上，导致测试脚本无法执行，Check 阶段整体失败。Docker 镜像的构建和推送阶段均已完成且成功。

### 与 PR 变更的关联
**与 PR 变更无关。** 该 PR 新增了 PostgreSQL 17.6 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 和 entrypoint.sh，Docker 镜像构建（`#8 DONE 268.4s`）和推送（`#11 DONE 58.0s`）均成功完成。失败发生在 CI 流水线的 [Check] 测试阶段，原因是 CI runner 上缺少 `shunit2` 测试框架依赖，属于 CI 基础设施问题，与 PR 的 Dockerfile 或 entrypoint.sh 代码无关。

日志证据：
- 构建阶段：`#8 DONE 268.4s`（PostgreSQL 编译安装完成）
- 推送阶段：`[Push] finished`，镜像 manifest 已推送
- Check 阶段表格为空（`+-------------+-------------+--------------+\n| Check Items | Description | Check Result |\n+-------------+-------------+--------------+`），说明测试根本未能运行

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 的测试环境中安装 `shunit2` 包。`shunit2` 是 Shell 脚本的 xUnit 风格单元测试框架，通常可通过系统包管理器安装（如 `dnf install shunit2` 或 `apt install shunit2`）。此问题与 PR 代码无关，无需修改 Dockerfile 或 entrypoint.sh。

## 需要进一步确认的点
- 确认 CI runner 镜像中是否应预装 `shunit2`，或是否需要由 CI 流水线在 [Check] 阶段前通过 `dnf install shunit2` 安装该依赖
- 确认其他成功通过 Check 的 PR 是否使用了不同的 runner 标签或 runner 镜像版本（当前 runner 可能缺少该包）
- 若 `shunit2` 在 openEuler 仓库中的包名不同（如 `shunit2` vs `shUnit2`），需确认正确的安装方式
