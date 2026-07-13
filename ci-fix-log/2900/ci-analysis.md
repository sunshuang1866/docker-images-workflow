# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: CI 测试框架依赖缺失
- 新模式症状关键词: shunit2, file not found, common_funs.sh, eulerpublisher, [Check] test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:18:18,902-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed

+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI 运行器环境中的测试脚本 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 测试框架依赖 `shunit2`（Unix shell 单元测试框架）在 CI 运行器中未安装或不在预期路径，导致 eulerpublisher 的 `[Check]` 阶段无法执行任何容器测试，测试结果表格为空（无 Check Items 行），最终判定为失败。

### 与 PR 变更的关联
**与 PR 无关。** PR 仅新增了一个 Dockerfile（`Others/httpd/2.4.66/24.03-lts-sp4/Dockerfile`）、一个启动脚本（`httpd-foreground`）以及更新了 README、doc/image-info.yml 和 meta.yml。Docker 镜像构建阶段全部成功完成（步骤 #10 至 #14 均标记为 DONE，镜像成功推送到目标仓库），失败仅发生在构建完成后的 CI `[Check]` 测试阶段。`shunit2: file not found` 是 CI 测试运行器自身的基础设施问题，非 PR 代码变更所能触发。

## 修复方向

### 方向 1（置信度: 中）
CI 运行器中缺失 `shunit2` 包。需确保 CI 测试节点已安装 `shunit2`（openEuler 中通过 `dnf install shunit2` 安装），或检查 `eulerpublisher` 包是否正确安装了其测试依赖。可通过在 CI 节点上执行 `rpm -q shunit2` 或 `find / -name 'shunit2' 2>/dev/null` 确认当前安装状态。

### 方向 2（置信度: 低）
若 `shunit2` 已安装但路径不对，可能是 `eulerpublisher` 或 `common_funs.sh` 中 `PATH` 配置未包含 `shunit2` 的安装路径（如 `/usr/share/shunit2`），需检查测试框架中的 source 路径配置。

## 需要进一步确认的点
- CI 测试节点上 `shunit2` 是否已安装（执行 `rpm -q shunit2` 或 `which shunit2`）
- 同类仓库中其他成功 PR 的 Check 阶段日志，确认 `shunit2` 是否仅在当前构建节点缺失（可能为特定 runner 的环境问题）
- `eulerpublisher` 包的依赖声明中是否已将 `shunit2` 列为必需依赖
- 本次 CI 构建分配到的 runner 节点编号，确认与该 runner 历史成功记录的差异

## 修复验证要求
无需针对此 PR 的 Dockerfile 做任何代码修改。验证修复是否生效的唯一方式是：在 CI 节点上修复 `shunit2` 安装问题后，重新触发 CI 构建，确认 `[Check]` 阶段能正常执行容器测试并产出有实际测试项的检查结果表格。
