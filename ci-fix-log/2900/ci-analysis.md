# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 缺少测试框架依赖
- 新模式症状关键词: shunit2, file not found, common_funs.sh, [Check] test failed

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
Notifying upstream projects of job completion
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`（CI Runner 测试环境）
- 失败原因: CI Runner 上的测试脚本 `common_funs.sh` 尝试通过 `.` (source) 加载 `shunit2` 测试框架，但该文件在 CI Runner 环境中不存在，导致 `[Check]` 阶段失败

### 与 PR 变更的关联
与 PR 变更**无关**。Docker 镜像构建（所有 7 个步骤均通过）和推送均已成功完成：
- `#9` — 下载解压 httpd 源码：通过
- `#10` — configure / make / make install：通过（41.6s）
- `#11` — groupadd / useradd / sed 配置：通过
- `#12` — COPY httpd-foreground：通过
- `#13` — chmod +x：通过
- `#14` — 导出并推送镜像到 docker.io：通过（日志明确显示 `[Build] finished` 和 `[Push] finished`）

失败仅发生在构建完成后的 `[Check]` 测试阶段，是 CI Runner 环境缺少 `shunit2` 测试框架所致，属于基础设施问题，与本次 PR 新增的 httpd 2.4.66-oe2403sp4 Dockerfile 无关。

## 修复方向

### 方向 1（置信度: 高）
在 CI Runner 上安装 `shunit2` 测试框架。`shunit2` 是 Shell 单元测试框架，在 openEuler 上可通过以下方式之一安装：
- `dnf install shunit2`（如 openEuler 仓库中有该包）
- 或从 GitHub 克隆 `kward/shunit2` 仓库并设置 `PATH`

此问题需要 CI 运维人员在构建节点上安装对应软件包，**code-fixer 无需处理**。

## 需要进一步确认的点
- `shunit2` 是仅在该特定 Runner 上缺失，还是整个 CI 集群的 Runner 均未安装（需 CI 运维确认）
- 之前同类镜像的 Check 阶段是否也使用 shunit2，若之前未触发此错误则可能是 Runner 环境变更导致

## 修复验证要求
无需验证（infra-error，与 PR 代码无关）。
