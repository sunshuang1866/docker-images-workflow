# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 缺少shunit2测试框架
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, Check test failed

## 根因分析

### 直接错误
```
2026-07-09 09:40:24,013 - INFO - [Check] checking ****test/postgres:17.6-oe2403sp4-x86_64 ...
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
- 失败原因: CI 的 [Check] 阶段（镜像构建后的 container 测试）在执行前即崩溃——测试框架脚本 `common_funs.sh` 第 13 行尝试 source `shunit2` 库文件，但该 shell 单元测试框架未安装在该 CI runner 上，导致所有检测项均未执行（结果表为空）。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 变更仅包括新增 Dockerfile、entrypoint.sh、README.md 更新和 meta.yml 更新。Docker 镜像构建阶段全部成功完成（`#8 DONE 268.4s`，configure → make → make install 全程无错误，`[Build] finished` 和 `[Push] finished` 均正常），镜像已成功构建并推送到 registry。失败发生在 `eulerpublisher` 工具的 [Check] 事后检测阶段，因 CI runner 缺少 `shunit2` 测试框架依赖而中断。

## 修复方向

### 方向 1（置信度: 中）
在 CI runner 环境中安装 `shunit2` 测试框架。`shunit2` 是一个标准的 Shell 脚本单元测试库，可通过以下方式之一安装：
- `dnf install shunit2`
- `pip install shunit2`
- 从 GitHub（`kward/shunit2`）克隆到 CI runner

此修复需由 CI 基础设施维护者操作，Code Fixer 无需处理。

### 方向 2（置信度: 低）
若 `shunit2` 已安装但在非预期路径，则需修正 `common_funs.sh` 中 source `shunit2` 的路径引用。此也为 CI 基础设施层面的问题。

## 需要进一步确认的点
1. 确认同一 CI runner 上其他同类镜像（如 postgres 17.6 on 24.03-lts-sp2）的 [Check] 阶段是否也失败。如果也失败，则可确认是 CI runner 环境普遍缺失 `shunit2`，而非本 PR 单独触发。
2. 确认该 CI runner 镜像中是否安装了 `shunit2` 包（运行 `which shunit2` 或 `rpm -qa | grep shunit2`）。
3. 确认 entrypoint.sh 在容器中是否能正常启动 PostgreSQL（手动 `docker run` 测试），以完全排除容器运行时问题的可能性——尽管当前日志证据明确指向 CI 框架层故障。
