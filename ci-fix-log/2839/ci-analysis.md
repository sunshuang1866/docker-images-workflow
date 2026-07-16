# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式（与模式39类似，均为 CI 工具依赖缺失）
- 新模式标题: CI检查框架缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, [Check] test failed, eulerpublisher

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 09:40:24,021-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: CI [Check] 阶段 — eulerpublisher 测试框架 `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`
- 失败原因: CI 节点的 eulerpublisher 测试环境缺少 `shunit2` shell 测试框架，导致 `common_funs.sh` 在 line 13 加载 `shunit2` 时失败，[Check] 阶段的容器健康检查无法执行

### 与 PR 变更的关联
**与 PR 变更无关**。PR 仅新增了 Postgres 17.6 在 openEuler 24.03-LTS-SP4 上的 Dockerfile、entrypoint.sh 及配套元数据。Docker 镜像的构建和推送均已成功完成（日志显示 `#8 DONE 268.4s`、`[Build] finished`、`[Push] finished`、`#11 DONE 58.0s`），镜像已成功推送到 registry。失败完全发生在镜像构建/推送完成之后的 CI 工具自身后处理阶段，属于 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner/workder 节点上安装 `shunit2` shell 测试框架包。`shunit2` 是 eulerpublisher 容器镜像健康检查测试的运行时依赖，缺失导致所有镜像的 [Check] 阶段均会失败。该问题应由 CI 运维团队处理，与 PR 代码无关。

## 需要进一步确认的点
- 确认 CI 节点上是否本应预装 `shunit2` 但因环境漂移导致缺失（检查其他最近成功的 PR 是否也在同一节点执行）
- 确认本 PR 的 aarch64 架构构建 job 是否因同一原因失败（日志仅包含 x86_64 构建输出）
- 注：Dockerfile 中 ENV 指令使用了旧版 `ENV key value` 格式（非 `ENV key=value`），构建日志中产生了 2 条 `LegacyKeyValueFormat` 警告，但这是非致命的 lint 级别提示，不影响构建结果
