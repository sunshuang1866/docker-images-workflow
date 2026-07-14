# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试框架缺依赖
- 新模式症状关键词: `shunit2: file not found`, `common_funs.sh`, `[Check] test failed`

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:18:18,902 CRITICAL: [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
```

### 根因定位
- 失败位置: CI Runner 上 `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`
- 失败原因: CI 容器镜像测试框架（`eulerpublisher` 的 `common_funs.sh`）在 `[Check]` 阶段尝试 `source shunit2`，但 `shunit2`（Shell 单元测试框架）未安装在该 CI Runner 上，导致测试脚本无法加载、Check 表为空，最终标记为失败。

### 与 PR 变更的关联
**与 PR 变更无关**。该 PR 新增的 Dockerfile 构建和推送阶段均已成功完成（`[Build] finished`、`[Push] finished`，镜像 `2.4.66-oe2403sp4-x86_64` 成功推送到 registry）。失败发生在 CI Runner 自身的测试框架初始化阶段（`[Check]`），是 CI 基础设施问题，httpd 镜像本身构建正确。

## 修复方向

### 方向 1（置信度: 高）
在 CI Runner 上安装 `shunit2` 包。对于 openEuler 系统，可尝试 `dnf install shunit2` 或从 GitHub（`kward/shunit2`）下载安装。安装后重新触发 CI 构建即可。

### 方向 2（置信度: 低）
如果 `shunit2` 已经在 Runner 上安装但仍找不到，检查 `common_funs.sh` 中 `shunit2` 的 source 路径是否正确（可能需要在 `PATH` 或明确指定绝对路径）。

## 需要进一步确认的点
1. 该 CI Runner 节点上是否已安装 `shunit2`：执行 `which shunit2` 或 `rpm -qa | grep shunit2` 确认。
2. `common_funs.sh` 第 13 行 `source shunit2` 的实际加载路径是什么——是否为相对路径、是否依赖 `PATH`。
3. 同一 Runner 上其他镜像（如已有 httpd 2.4.66-oe2403sp2）的 Check 阶段是否也因同样原因失败，以排除 Runner 环境变更或首次运行的问题。
