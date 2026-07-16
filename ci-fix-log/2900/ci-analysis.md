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
2026-07-10 09:18:18,902 - CRITICAL - [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI Worker 测试环境（`/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`）
- 失败原因: CI 的 [Check] 阶段在执行镜像集成测试时，`common_funs.sh` 脚本尝试通过 `.` 命令 source `shunit2`（Shell 单元测试框架），但 `shunit2` 未安装在 CI runner 上，导致所有测试检查项均无法执行，Check 步骤被标记为失败。Docker 镜像的构建（Build）和推送（Push）阶段均已成功完成。

### 与 PR 变更的关联
与 PR 变更**无关**。PR 新增的 Dockerfile 构建完全成功：所有 7 个 RUN 步骤通过，镜像成功编译并推送到 registry（`#14 DONE 31.3s`，`[Build] finished`，`[Push] finished`）。失败发生在 CI 基础设施层的测试框架（`eulerpublisher` 的 Check 模块），属于 CI worker 环境不完整导致。

## 修复方向

### 方向 1（置信度: 高）
在 CI worker 节点上安装 `shunit2` 包（Shell 单元测试框架）。Check 阶段的 `common_funs.sh` 脚本依赖 `shunit2` 来执行容器镜像的集成验证测试（如容器启动、端口监听等）。安装后重新触发 CI 即可通过。

## 需要进一步确认的点
- 确认 CI worker 环境的操作系统包管理器中 `shunit2` 的包名（如 `shunit2` 或 `shunit2-sh`）。
- 确认 PR 中新增的 `httpd-foreground` 脚本和 `httpd.conf` sed 配置在容器运行时是否正确——由于 Check 测试未执行，容器组件的运行时行为未得到验证。
