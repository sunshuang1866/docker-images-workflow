# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试框架缺失
- 新模式症状关键词: shunit2: file not found, common_funs.sh, Check test failed

## 根因分析

### 直接错误
```
2026-07-10 09:18:18,896 - INFO - [Check] checking ****test/httpd:2.4.66-oe2403sp4-x86_64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
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
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh`:13
- 失败原因: CI 运行环境中的 `eulerpublisher` 测试框架依赖 `shunit2`（一个 Shell 单元测试库），但该库未安装在当前 CI runner 上，导致 `source shunit2` 时报 `file not found`，进而使整个 [Check] 阶段失败。

### 与 PR 变更的关联
**此失败与 PR 变更无关。** Docker 镜像的构建（BUILD）和推送（PUSH）阶段均已完成且成功：
- 所有 Dockerfile RUN 步骤（#9-#13）均以 `DONE` 状态完成
- `#14 exporting to image` 成功导出并推送了镜像 `docker.io/****test/httpd:2.4.66-oe2403sp4-x86_64`
- 日志中明确记录：`[Build] finished`、`[Push] finished`

失败仅发生在 CI 自身的 [Check] 阶段，原因是 CI runner 上缺少 `shunit2` 库，属于基础设施环境问题，而非 PR 新增的 Dockerfile、httpd-foreground 脚本或元数据文件导致的。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 镜像或部署脚本中安装 `shunit2` 测试框架。openEuler 系统上可通过 `dnf install shunit2` 安装，或从 `https://github.com/kward/shunit2` 将 `shunit2` 脚本部署到 `/usr/local/etc/eulerpublisher/tests/container/common/` 目录下，使 `common_funs.sh` 中的 `source shunit2` 能正常解析。

## 需要进一步确认的点
1. 确认其他在本 CI runner 上构建的 PR 是否也因相同的 `shunit2: file not found` 错误而失败——如果普遍存在，说明是 CI 基础设施的整体问题。
2. 确认 CI runner 的操作系统版本（openEuler 24.03-LTS-SP4 对应的 runner）是否默认包含 `shunit2` 包，或是否需要作为 CI 环境初始化的一部分显式安装。
3. 如果 `shunit2` 已安装但路径不在 `common_funs.sh` 的 `PATH` 搜索范围内，需确认 `shunit2` 的目标安装路径与 `common_funs.sh` 中预期的 source 路径是否一致。
