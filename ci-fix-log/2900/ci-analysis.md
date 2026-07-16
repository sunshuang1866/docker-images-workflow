# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2测试框架缺失
- 新模式症状关键词: `shunit2: file not found`, `common_funs.sh`, `[Check] test failed`

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
- 失败位置: CI [Check] 阶段，`eulerpublisher` 测试脚本 `common_funs.sh:13`
- 失败原因: CI runner 的测试环境中未安装 `shunit2`（shell 单元测试框架），导致 `common_funs.sh` 在 source 该库时失败（`shunit2: file not found`）。Docker 构建和镜像推送均已成功完成。

### 与 PR 变更的关联
**与 PR 无关**。PR 新增了 httpd 2.4.66 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及配套文件（httpd-foreground、meta.yml、README.md、image-info.yml）。Docker 镜像构建全过程成功：
- 源码下载、configure、make、make install 均正常完成（#10 DONE 41.6s）
- groupadd/useradd 及配置文件修改正常完成（#11 DONE 0.1s）
- COPY 和 chmod 步骤正常（#12、#13）
- 镜像导出并推送至仓库成功（#14 DONE 31.3s，`[Build] finished`，`[Push] finished`）

失败仅发生在构建完成后的 [Check] 容器测试阶段，因 CI runner 缺少 `shunit2` 依赖导致测试脚本无法运行，**并非 PR 代码问题**。

## 修复方向

### 方向 1（置信度: 高）
CI 基础设施问题：在 CI runner（或 eulerpublisher 所在的测试节点）上安装 `shunit2` shell 测试框架。openEuler 中可通过 `dnf install shunit2` 安装该包，或在测试脚本中调整 shunit2 的 source 路径指向 CI 部署的 shunit2 位置。此问题需由 CI 运维人员处理，**Code Fixer 无需修改 Dockerfile**。

## 需要进一步确认的点
- 确认 CI runner 的 openEuler 版本是否已包含 `shunit2` RPM 包，若未包含需从 EPOL 或其他源安装。
- 若 shunit2 是 eulerpublisher 工具链的一部分，确认其部署流程是否遗漏了该依赖的安装步骤。
- 确认同批次其他 PR 的 [Check] 阶段是否也有相同的 shunit2 缺失问题（若是，则确认为 CI 环境全局问题而非本次 PR 引入）。
