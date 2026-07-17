# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试依赖缺失
- 新模式症状关键词: shunit2: file not found, eulerpublisher, Check test failed

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
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 测试框架 `eulerpublisher` 的容器检查阶段（`[Check]`），测试脚本 `common_funs.sh` 尝试通过 `. shunit2` 引入 `shunit2` shell 测试库，但该库在 CI runner 上未安装/不可用，导致所有测试项（Check Items 表为空）均无法执行。

### 与 PR 变更的关联
**与 PR 变更无关。** Docker 镜像构建和推送阶段全部成功完成：
- `#10 DONE 41.6s`（make && make install 成功）
- `#11 DONE 0.1s`（groupadd/useradd/sed 配置成功）
- `#12 DONE 0.0s`（COPY httpd-foreground 成功）
- `#13 DONE 0.1s`（chmod 成功）
- `#14 DONE 31.3s`（镜像导出、manifest 创建、推送到 docker.io 全部成功）
- 日志明确记录 `[Build] finished` 和 `[Push] finished`

失败仅发生在构建之后的 `[Check]` 阶段——`eulerpublisher` 测试工具自身的 Shell 测试框架缺少 `shunit2` 依赖，与本次 PR 新增的 httpd Dockerfile、httpd-foreground 脚本、README 文档等改动均无关联。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境中安装 `shunit2` shell 测试框架。这是纯粹的 CI 基础设施问题——`eulerpublisher` 的容器检查测试脚本依赖 `shunit2` 库，但执行环境中未安装该依赖，导致所有镜像的 `[Check]` 阶段均无法运行。需由 CI 运维团队在构建节点上安装 `shunit2`（可通过包管理器或手动部署到 `/usr/local/etc/eulerpublisher/tests/` 可找到的路径）。

## 需要进一步确认的点
- 确认 `shunit2` 在 CI runner 上的预期安装路径是否为 `/usr/local/etc/eulerpublisher/tests/container/common/` 或系统 `PATH` 中的某个位置
- 确认 `shunit2` 缺失是本节点特有还是所有 CI 节点都存在（若是本节点特有，重试流水线可能在其他节点上通过）

## 修复验证要求
无。此问题为 CI 基础设施缺陷，与 PR 代码变更无关，Code Fixer 无需对 Dockerfile 或任何仓库文件进行修改。
