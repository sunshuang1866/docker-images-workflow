# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 检查工具shunit2缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, eulerpublisher, [Check] test failed

## 根因分析

### 直接错误
```
[Build] finished
[Push] finished
[Check] checking ****test/postgres:17.6-oe2403sp4-x86_64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
CRITICAL: [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Finished: FAILURE
```

### 根因定位
- 失败位置: CI runner 的 `eulerpublisher` 测试基础设施，具体为 `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`
- 失败原因: CI 流水线的 `[Check]` 后置验证阶段调用 `common_funs.sh`（容器镜像检查框架），该脚本第 13 行引用了 `shunit2`（Shell 脚本单元测试框架），但 CI runner 环境中未安装 `shunit2` 或未将其加入 PATH。

### 与 PR 变更的关联
**与 PR 变更无关。** Docker 镜像的构建（PostgreSQL 17.6 源码编译）和推送均已成功完成（`[Build] finished` / `[Push] finished`）。PR 新增的 Dockerfile 和 entrypoint.sh 未引入任何构建错误。失败发生在 CI 流水线的后置检查阶段，完全由 CI runner 环境缺少 `shunit2` 工具导致。

## 修复方向

### 方向 1（置信度: 中）
在运行该镜像 Check 测试的 CI runner 上安装 `shunit2` 包。`shunit2` 是标准的 Shell 测试框架，openEuler 系统中通常可通过 `dnf install shunit2` 或从 EPOL 仓库安装。若 openEuler 软件源中无此包，可从 GitHub（`kward/shunit2`）下载并放置到 CI runner 的 PATH 可访问路径中。

### 方向 2（置信度: 低）
若 `shunit2` 应当由 `eulerpublisher` 自身打包提供而非依赖系统安装，则需在 `eulerpublisher` 的安装/部署流程中将 `shunit2` 纳入依赖。此方向需要先确认 `eulerpublisher` 的项目规范中对测试依赖的管理方式。

## 需要进一步确认的点
1. 同一 CI runner（或同一架构的 runner）上，其他数据库镜像（如 postgres 17.6-oe2403sp2）的 `[Check]` 测试是否也因相同原因失败。如果是，则为 runner 级别的基础设施缺失；如果否，则说明 `shunit2` 的安装在该 runner 上被意外移除或从未安装。
2. `shunit2` 在 openEuler 24.03-LTS-SP4（runner 所在系统）的软件源中是否可用，包名是 `shunit2` 还是其他名称（如 `ShellUnit`）。
3. `eulerpublisher` 的测试框架是否在某个版本中新增了对 `shunit2` 的依赖，而 CI runner 尚未更新。

## 修复验证要求
由于此失败为 `infra-error`，修复不涉及代码变更。验证方式为在目标 CI runner 上确认 `shunit2` 安装后，重新触发 PR #2839 的 CI 流水线，检查 `[Check]` 阶段是否通过。
