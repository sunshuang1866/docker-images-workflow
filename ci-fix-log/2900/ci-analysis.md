# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2测试工具缺失
- 新模式症状关键词: shunit2, file not found, common_funs.sh, Check test failed

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
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 测试阶段，`common_funs.sh` 脚本尝试 `source shunit2`（`line 13: .: shunit2: file not found`），但 `shunit2` shell 单元测试框架未安装在 CI runner 上，导致 [Check] 阶段的容器测试无法执行，测试结果表格全部为空，最终 CI 判定为失败。

### 与 PR 变更的关联
**与 PR 无关。** 本次 PR 新增了 httpd 2.4.66 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及相关元数据文件。Docker 构建阶段全部成功完成（步骤 #9 源码下载编译、#10 make install、#11 配置、#12-13 COPY/chmod、#14 构建并推送镜像，总耗时约 72s，无任何编译或运行时错误）。失败发生在构建完成之后的 CI [Check] 阶段，因 CI runner 环境缺少 `shunit2` 测试工具所致，与 PR 的代码变更完全无关。

## 修复方向

### 方向 1（置信度: 高）
CI runner 环境中安装 `shunit2` 测试框架。在 CI 执行节点上运行 `dnf install -y shunit2` 或等效命令，确保 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh` 脚本中 `source shunit2` 能找到该库。此为 CI 基础设施问题，无需修改 Dockerfile 或任何 PR 代码。

## 需要进一步确认的点
- 确认 `shunit2` 在 openEuler 软件源中的包名（可能为 `shunit2` 或 `shunit`）
- 确认是否需要为 openEuler 24.03-LTS-SP4 新变体配置对应的容器测试用例（当前测试表格为空，可能是新变体尚无定制测试覆盖）
- 确认同一 CI 流水线中其他 openEuler SP4 变体的镜像（如 SP2 的 httpd 2.4.66）是否能通过 Check 阶段，以排除 `shunit2` 缺失是否为该 runner 偶发故障
