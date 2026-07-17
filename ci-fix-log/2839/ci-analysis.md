# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试框架shunit2缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, [Check] test failed

## 根因分析

### 直接错误
```
2026-07-09 09:40:24,013 - INFO - [Check] checking ****test/postgres:17.6-oe2403sp4-x86_64 ...
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
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 测试框架依赖的 `shunit2`（Shell 单元测试框架）在 CI runner 环境中不存在，导致 `common_funs.sh` 脚本执行 `shunit2` 命令时报 "No such file or directory"，Check 阶段无法执行任何测试用例（Check Items 表格完全为空），最终 CI pipeline 判定构建失败。

### 与 PR 变更的关联
**无关**。本次 PR 仅新增了 PostgreSQL 17.6 在 openEuler 24.03-LTS-SP4 上的 Dockerfile、entrypoint.sh、meta.yml 条目和 README.md 记录。日志显示 Docker 镜像构建（make install 完整通过）和推送均成功：
- `#8 DONE 268.4s` — 编译安装成功
- `#11 pushing layers 43.0s done` — 镜像推送成功
- `[Build] finished` / `[Push] finished` — 构建和推送阶段正常结束

失败仅发生在后续的 `[Check]` 镜像验证阶段，原因是 CI runner 缺少 `shunit2` 测试框架，与 PR 的代码变更无关。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境中安装 `shunit2` 测试框架。`shunit2` 是一个 Shell 脚本单元测试库（项目地址: https://github.com/kward/shunit2），需要在执行 `eulerpublisher` 的 [Check] 步骤之前，确保 `shunit2` 可执行文件位于 `PATH` 中（或安装到 `/usr/local/etc/eulerpublisher/tests/container/app/../common/` 所引用的位置）。例如在 CI pipeline 的 pre-check 阶段添加 `yum install shunit2` 或通过 `git clone` 获取 shunit2 源码并设置路径。

## 需要进一步确认的点
1. 同一 CI runner 上其他镜像（如 PostgreSQL 17.6 的 `24.03-lts-sp2` 变体、其他应用镜像）的 [Check] 是否也因相同的 `shunit2` 缺失而失败？如果仅此 PR 失败，需确认是否有 runner 调度差异。
2. `common_funs.sh` 中 `shunit2` 的预期安装路径是什么？是否有预定义的目录（如 `/usr/local/share/shunit2`）需要将其加入 `PATH`？
3. 是否需要由 `eulerpublisher` 安装包自身提供 `shunit2` 依赖声明（类似 Python 的 `requirements.txt`）？

## 修复验证要求
无需 code-fixer 验证。本失败为 CI 基础设施问题（infra-error），不涉及对 Dockerfile、entrypoint.sh 或任何 PR 代码文件的修改。修复由 CI 运维人员完成，code-fixer 无需处理。
