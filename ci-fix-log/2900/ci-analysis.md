# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: CI测试框架依赖缺失
- 新模式症状关键词: shunit2, file not found, common_funs.sh, eulerpublisher, Check test failed

## 根因分析

### 直接错误
```
2026-07-10 09:18:18,896-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:161]-INFO: [Check] checking ****test/httpd:2.4.66-oe2403sp4-x86_64 ...
2026-07-10 09:18:18,896 - INFO - [Check] checking ****test/httpd:2.4.66-oe2403sp4-x86_64 ...
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
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`
- 失败原因: CI 检查阶段的测试脚本 `common_funs.sh` 第 13 行尝试 `source` 或 `.` 引入 `shunit2` shell 单元测试框架，但该框架未安装或不在 `PATH` 中，导致 Check 阶段无法执行任何测试即失败。

### 与 PR 变更的关联
**与本次 PR 改动无关。** PR #2900 仅新增了以下文件：
- `Others/httpd/2.4.66/24.03-lts-sp4/Dockerfile`（httpd 构建步骤全部成功）
- `Others/httpd/2.4.66/24.03-lts-sp4/httpd-foreground`（启动脚本）
- 更新 `README.md`、`doc/image-info.yml`、`meta.yml` 等文档/元数据文件

Docker 镜像构建阶段（#1-#14）全部成功完成，镜像已成功构建并推送到 registry。失败发生在构建完成后的 `[Check]` 阶段，该阶段由 CI 工具 `eulerpublisher` 调用 `shunit2` 对所构建的镜像执行验证测试，`shunit2` 在 CI runner 上不可用导致整个 Check 阶段崩溃。

## 修复方向

### 方向 1（置信度: 中）
CI 运维人员应在执行检查任务的 runner 上安装 `shunit2` shell 测试框架。`shunit2` 通常可从 EPEL 仓库或 GitHub（`kward/shunit2`）获取。安装后重新触发 CI 即可通过。

### 方向 2（置信度: 低）
如果 `shunit2` 已安装但路径配置有误，需检查 `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh` 第 13 行中 `shunit2` 的引用方式（是通过绝对路径查找还是依赖 `PATH`），并修正路径或将 `shunit2` 所在目录加入 `PATH`。

## 需要进一步确认的点
1. 确认 CI runner 上 `shunit2` 是否曾经可用：检查同 runner 上其他成功过的 httpd 镜像（如 `2.4.66-oe2403sp2`）在 Check 阶段是否使用了相同的 `common_funs.sh` 且能正常通过，以排除本次是否为 runner 配置变更导致。
2. 确认 `eulerpublisher` 的 `common_funs.sh` 中对 `shunit2` 的引用方式（绝对路径 vs 依赖 PATH），以及 CI 环境中 `shunit2` 的安装位置。
3. 如果其他 httpd 镜像的 Check 也使用了同一套测试脚本且同样失败，说明是 CI 基础设施的全局问题；如果仅本 PR 失败，则可能是特定 runner 节点的问题。
