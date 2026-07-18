# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2测试框架缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, eulerpublisher, Check

## 根因分析

### 直接错误
```
[Check] checking ****test/postgres:17.6-oe2403sp4-x86_64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
[Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 测试环境（eulerpublisher 的 [Check] 阶段）缺少 `shunit2` 测试框架（bash 单元测试库），导致 `common_funs.sh` 脚本在 source `shunit2` 时失败，所有测试用例无法加载和执行，检查结果表为空。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 证据：
1. Docker 镜像构建完全成功（`#8 DONE 268.4s`，所有 10 个 Dockerfile 步骤均通过），`[Build] finished` 和 `[Push] finished` 日志确认镜像已成功构建并推送至 `docker.io/****test/postgres:17.6-oe2403sp4-x86_64`。
2. 失败发生在 CI 工具 `eulerpublisher` 的 [Check]（容器运行时测试）阶段，但错误并非来自容器内部——`shunit2` 是 CI runner 宿主机上的 bash 测试框架，用于编排测试用例。该框架缺失使得测试**未能实际执行**，检查结果表完全为空。
3. PR 变更仅新增 PostgreSQL 17.6 在 openEuler 24.03-LTS-SP4 上的 Dockerfile、entrypoint.sh、README 条目和 meta.yml 条目，不涉及 CI 测试基础设施配置。
4. Docker 构建日志中存在两个非致命的 `LegacyKeyValueFormat` 警告（Dockerfile 第 26、30 行使用了旧式 `ENV key value` 格式），但警告不会导致构建失败，且与 `shunit2` 缺失无关联。

## 修复方向

### 方向 1（置信度: 高）
CI 基础设施层面修复：在运行 postgres 容器检查的 CI runner/环境上安装 `shunit2` 测试框架。这属于 CI 运维工作，**Code Fixer 无需对 PR 代码做任何修改**。具体操作：在 CI pipeline 的测试阶段执行前，通过包管理器（如 `dnf install shunit2` 或 `git clone https://github.com/kward/shunit2` 并设置 `PATH`）确保 `shunit2` 可被 `common_funs.sh` 的 `source` 命令找到。

### 方向 2（可选，置信度: 低）
若 `shunit2` 的缺失是 openEuler 24.03-LTS-SP4 特定的（即其他平台 runner 上 `shunit2` 正常可用），则可能是该平台对应的 CI runner 镜像/环境配置不完整，CI 管理员需要为 24.03-LTS-SP4 的测试环境补充 `shunit2` 安装。

## 需要进一步确认的点
1. 同仓库中其他使用 openEuler 24.03-LTS-SP4 基础镜像的 Dockerfile（如 `Database/postgres/17.6/24.03-lts-sp2/` 等）的 [Check] 阶段是否也因缺少 `shunit2` 而失败，以判断这是否为 24.03-LTS-SP4 平台 CI runner 的共性问题。
2. 该 CI 测试环境是否有统一的 `shunit2` 安装基线，排查最近 runner 镜像更新是否无意中移除了该依赖。
3. 确认 `common_funs.sh` 脚本引用的 `shunit2` 路径是否正确——脚本中 `source shunit2` 依赖 `PATH` 环境变量，若 `shunit2` 安装在其他路径则需调整引用或添加软链接。
