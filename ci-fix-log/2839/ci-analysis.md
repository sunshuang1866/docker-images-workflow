# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式（参考 模式39：CI工具依赖缺失）
- 新模式标题: CI测试框架缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, [Check] test failed

## 根因分析

### 直接错误
```
2026-07-09 09:40:24,013 - INFO - [Check] checking ****test/postgres:17.6-oe2403sp4-x86_64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 09:40:24,021 - CRITICAL - [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 的 [Check] 阶段中，测试公共脚本 `common_funs.sh` 尝试加载 shell 测试框架 `shunit2`，但该工具在 CI runner 环境中不存在，导致所有 Check 测试无法执行、表格为空，`eulerpublisher` 报 `CRITICAL: [Check] test failed`。

### 与 PR 变更的关联
**与 PR 无关。** 该 PR 新增 4 个文件（Dockerfile、entrypoint.sh、README.md 更新、meta.yml 更新），Docker 镜像构建和推送均已成功完成：
- `#8 DONE 268.4s` — PostgreSQL 17.6 源码编译安装完成
- `#9 DONE` — COPY entrypoint.sh 完成
- `#10 DONE` — RUN chmod 完成
- `#11 DONE 58.0s` — 镜像 export + push 完成
- `[Build] finished`、`[Push] finished` 日志确认构建和推送均成功

失败仅发生在 `eulerpublisher` 工具链的 [Check] 阶段，属于 CI 基础设施层面的问题（runner 缺少 `shunit2` 测试框架），与 PR 的 Dockerfile、entrypoint.sh 等代码变更无任何关联。

## 修复方向

### 方向 1（置信度: 高）
**由 CI 运维团队处理**：在 CI runner 镜像或构建环境中安装 `shunit2` 测试框架（可通过包管理器安装或预置到 runner 的 PATH 中）。这不是代码仓库层面的问题，无需修改 PR 中的任何文件。

### 方向 2（可选）
若 `shunit2` 是预期由 eulerpublisher 自身绑定的测试依赖，需检查 `eulerpublisher` 包的部署是否完整，确认 `shunit2` 脚本是否被遗漏在安装包中。

## 需要进一步确认的点
- 确认 `shunit2` 是否应为 CI runner 预装的工具，还是 `eulerpublisher` 容器测试包的捆绑依赖。
- 确认同一 CI 环境中其他镜像（如其他 postgres 版本、其他 Database 镜像）的 Check 阶段是否也遇到相同的 `shunit2` 缺失——若同批次其他 job 均失败，可确认是 CI 基础设施全局问题。
