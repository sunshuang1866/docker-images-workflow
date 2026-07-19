# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2测试框架缺失
- 新模式症状关键词: shunit2: No such file or directory, common_funs.sh, eulerpublisher, [Check] test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 09:40:24,021-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI Check 阶段（`eulerpublisher` 测试框架）
- 失败原因: CI runner 环境中缺少 `shunit2` shell 单元测试框架，导致 `common_funs.sh` 无法 source 该库，[Check] 阶段的所有容器测试均未执行即失败。

### 与 PR 变更的关联
**与 PR 无关**。Docker 镜像构建（`make -j $(nproc)` 编译 PostgreSQL 17.6→ `make install`→ Docker image build）和镜像推送（`[Build] finished`、`[Push] finished`）均成功完成。日志中 Docker BuildKit 的两个 Warning（`LegacyKeyValueFormat: "ENV key=value"`）也仅为格式建议，非致命错误。失败发生在 CI 编排工具 `eulerpublisher` 的 [Check] 阶段，该阶段尝试运行容器功能测试但因为 `shunit2` 未安装而无法执行。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境中安装 `shunit2` 包。`shunit2` 是 `eulerpublisher` 测试框架的运行时依赖，缺失会导致所有容器镜像的 [Check] 阶段失败。此为 CI 基础设施问题，Code Fixer 无需对 PR 代码做任何修改。

### 方向 2（置信度: 低）
若无法在 CI runner 上安装 `shunit2`，可检查 `eulerpublisher` 测试框架是否支持跳过 Check 阶段或将其配置为可选（不影响 CI 整体通过/失败判定）。但此方向属于 CI 流水线配置调整，同样不涉及 PR 代码变更。

## 需要进一步确认的点
- `shunit2` 是否为该 CI runner 镜像的标准预装软件？若此前其他 PR 的 Check 阶段也曾失败并伴随相同报错，则可确认是 CI 环境配置缺失。
- `eulerpublisher` 的 `common_funs.sh` 中 `shunit2` 的 source 路径是否正确？是否存在安装路径不一致的情况。

## 修复验证要求
不涉及正则 patch 外部源文件，无需额外验证步骤。
