# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: shunit2 测试框架缺失
- 新模式症状关键词: shunit2, file not found, Check test failed, common_funs.sh

## 根因分析

### 直接错误
```
2026-07-10 09:18:18,896 - INFO - [Check] checking ****test/httpd:2.4.66-oe2403sp4-x86_64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:18:18,902 - CRITICAL - [Check] test failed
```

Check 结果表为空，无任何测试实际执行：
```
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI Runner 环境中缺少 `shunit2` shell 测试框架，`common_funs.sh` 第 13 行的 `. shunit2` source 命令找不到该文件，导致 [Check] 阶段在 6ms 内立即失败，所有容器测试未执行。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 变更仅新增 httpd 2.4.66 在 openEuler 24.03-LTS-SP4 上的 Dockerfile、启动脚本及相关元数据文件。Docker 镜像构建和推送均成功（`[Build] finished`、`[Push] finished`），所有 7 个 Dockerfile 步骤正常完成，构建输出 `#14 DONE 31.3s`。失败发生在 CI 基础设施层的 [Check] 测试阶段，属于 Runner 环境配置问题，非代码问题。

## 修复方向

### 方向 1（置信度: 中）
CI Runner 环境缺少 `shunit2` 包。需在 CI Runner 上安装 `shunit2`（openEuler 中包名可能为 `shunit2`），或在测试脚本的 PATH 中放置 `shunit2` 脚本文件。此修复在 CI 基础设施侧，不在代码仓库侧。

### 方向 2（可选，置信度: 低）
若 `shunit2` 在其他 Runner 上工作正常，则可能是该特定 Runner 节点的环境异常或被意外清理。尝试重新触发 CI 或将任务重新调度到另一节点可能消除问题。

## 需要进一步确认的点
1. `shunit2` 是否已在其他正在正常通过 CI 的 Runner 节点上安装？如果其他 PR 的 [Check] 阶段正常通过，说明 `shunit2` 只在当前 Runner 缺失。
2. `common_funs.sh` 中 `shunit2` 的期望安装路径是什么？（如 `/usr/bin/shunit2`、`/usr/share/shunit2/shunit2`）
3. 当前 Runner 节点（x86_64）是否为新部署的节点，遗漏了 `shunit2` 依赖的安装步骤？
4. openEuler 24.03-LTS-SP4 仓库中是否提供 `shunit2` 包？若未提供，需确认 CI Runner 上 `shunit2` 的安装方式（pip / 手动部署脚本）。
