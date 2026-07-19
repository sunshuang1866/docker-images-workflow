# CI 失败分析报告

## 基本信息
- PR: #2893 — chore(bind9): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2 测试框架缺失
- 新模式症状关键词: `shunit2: file not found`, `common_funs.sh`, `Check test failed`

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:24:00,662-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-10 09:24:00,662 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI Check 阶段 — `eulerpublisher` 测试框架的 `common_funs.sh` 第 13 行
- 失败原因: CI runner 环境中未安装 `shunit2` shell 测试框架，导致 `common_funs.sh` 中 `source shunit2` 失败，整个 Check 阶段在测试脚本启动前即崩溃

### 与 PR 变更的关联
PR 变更与此次失败**无关**。Docker 镜像构建（编译 422 个 C 源文件、链接、安装）和推送均已完成且成功：
- `#9 DONE 41.4s`（meson 编译 + 安装全部通过）
- `#10` ~ `#12` Dockerfile 其余步骤均 `DONE`
- `#13 exporting to image` + pushing 完成
- `[Build] finished`、`[Push] finished` 均已记录

失败仅发生在 eulerpublisher CI 工具的 `[Check]` 后置测试阶段，因 `shunit2` 未安装在 runner 环境中导致测试脚本无法加载，与 Dockerfile 内容、bind9 编译过程、镜像产物无关。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境中安装 `shunit2` 测试框架。`shunit2` 是 eulerpublisher 容器镜像检查流程的运行时依赖，需确保所有执行 Check 阶段的 runner 均已预装该工具。

## 需要进一步确认的点
- 确认 CI runner 镜像/环境中 `shunit2` 的预期安装路径（`common_funs.sh` 第 13 行 `source shunit2` 依赖 `PATH` 或特定路径）
- 确认该 runner 是否与其他成功通过 Check 阶段的 runner 共享同一个环境模板，以及 shunit2 是否存在版本或路径差异
- 确认是否仅有 aarch64 runner 存在此问题（目前日志只显示了 aarch64 架构的构建和检查），amd64 runner 是否也因同样原因失败

## 修复验证要求
无需代码修复。此失败为 CI 基础设施问题（测试环境缺少 shunit2），Code Fixer 无需处理。待 CI 运维团队修复 runner 环境（安装 shunit2）后，重新触发构建即可通过。
