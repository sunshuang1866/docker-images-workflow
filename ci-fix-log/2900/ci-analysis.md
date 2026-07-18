# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2测试框架缺失
- 新模式症状关键词: shunit2, file not found, common_funs.sh, eulerpublisher, Check test failed

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
- 失败位置: 不适用（CI 基础设施层面）
- 失败原因: CI 的 `[Check]` 测试阶段，测试脚本 `common_funs.sh` 尝试 source 加载 `shunit2` 单元测试框架，但该框架未安装在 CI runner 的执行环境中，导致 check 阶段失败。Docker 镜像的构建和推送均已成功完成。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 新增的 Dockerfile（`Others/httpd/2.4.66/24.03-lts-sp4/Dockerfile`）构建完全成功：
- 源码下载、解压、编译（`./configure && make && make install`）全部通过（步骤 `#10 DONE 41.6s`）
- Dockerfile 中所有 7 个 RUN 步骤全部成功（`#11 DONE 0.1s`、`#13 DONE 0.1s` 等）
- 镜像导出并推送成功（`#14 exporting to image ... pushing layers 15.8s done`）
- CI 日志明确记录 `[Build] finished`、`[Push] finished`

失败仅发生在编译构建完成之后的 `[Check]` 阶段，属于 CI 平台测试基础设施（`eulerpublisher` 工具链）的问题。

## 修复方向

### 方向 1（置信度: 高）
向 CI 运维团队报告：CI runner 的 `eulerpublisher` 测试环境中缺少 `shunit2` 测试框架，导致 `[Check]` 阶段无法运行。需要在 CI runner 镜像或执行环境中安装 `shunit2` 包（可通过 `dnf install shunit2` 或从源码部署）。修复后重新触发 CI 即可通过。

### 方向 2（置信度: 低）
如果短期无法恢复 CI 环境的 `shunit2`，可临时将 `meta.yml` 中的 `2.4.66-oe2403sp4` 条目标记为无需 check，但此做法不推荐，仅作临时过渡方案。

## 需要进一步确认的点
1. 确认 CI runner 环境中是否预期应安装 `shunit2`，以及该依赖是否有版本变更记录。
2. 确认是否只有该特定架构的 runner 缺少 `shunit2`（日志仅展示了 x86_64 构建，需确认 aarch64 runner 状态）。
3. 确认 `shunit2` 在 openEuler 24.03 仓库中的包名是否为 `shunit2`（与 `dnf search shunit2` 确认）。

## 修复验证要求
不适用（此失败为 infra-error，无需修改 PR 代码，修复需运维侧处理 CI runner 环境）。
