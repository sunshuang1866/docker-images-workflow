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
2026-07-10 09:18:18,896 - INFO - [Check] checking ****test/httpd:2.4.66-oe2403sp4-x86_64 ...
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
- 失败位置: CI [Check] 阶段 — `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI runner 环境中缺少 `shunit2` shell 测试框架，`common_funs.sh` 脚本第 13 行的 `. shunit2` source 命令找不到该文件，导致整个测试阶段无法执行，所有 [Check] 检查项结果全部为空。

### 与 PR 变更的关联
**本次 PR 变更不直接触发此失败。** PR 仅新增了 httpd 2.4.66 在 openEuler 24.03-LTS-SP4 上的 Dockerfile、启动脚本及元数据文件。Docker 镜像构建（Build）和推送（Push）阶段均成功完成（日志中 step #9-#14 全部 `DONE`），失败仅发生在 CI 的容器测试（[Check]）阶段，且原因是 CI runner 上 `shunit2` 未安装或不在 `PATH` 中。该问题与 PR 代码变更无关，属于 CI 基础设施层面的缺失。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境中安装 `shunit2` shell 测试框架。具体操作：运维人员在执行该 job 的 CI agent 上通过包管理器安装 `shunit2`（如在 openEuler 上 `dnf install shunit2`），或将 `shunit2` 部署到 `common_funs.sh` 期望的 `PATH` 路径下，确保 [Check] 阶段的测试框架可用。

## 需要进一步确认的点
- 确认 CI runner 节点上 `shunit2` 是否确实未安装，以及其它同类镜像的 [Check] 阶段是否也因同样原因全部失败（即是否为该 runner 节点的全局问题，还是仅本次构建的临时环境异常）。
- 确认 `shunit2` 在 openEuler 仓库中的包名（可能是 `shunit2` 或 `shunit2-ng`），以及 CI runner 使用的操作系统版本是否支持直接安装该包。

## 修复验证要求
无需对此 PR 的代码做任何修改。修复后重新触发 CI 构建，确认 [Check] 阶段的测试表格能正常填充结果，整个 workflow 以 `Finished: SUCCESS` 结束即可。
