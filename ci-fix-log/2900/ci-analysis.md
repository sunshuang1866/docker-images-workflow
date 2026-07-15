# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI shunit2 缺失
- 新模式症状关键词: shunit2, file not found, common_funs.sh, eulerpublisher

## 根因分析

### 直接错误
```
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
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 的 [Check] 阶段中，`common_funs.sh` 脚本尝试通过 `.`（source）命令加载 `shunit2` shell 测试框架，但该文件在 CI runner 上不存在（`file not found`）。

### 与 PR 变更的关联
**与 PR 变更无关。** Docker 镜像构建（`[Build] finished`）和推送（`[Push] finished`）两个阶段均成功完成，所有 7 个 Dockerfile RUN 步骤均返回 `DONE`，镜像已成功导出并推送到 registry (`docker.io/****test/httpd:2.4.66-oe2403sp4-x86_64`)。失败仅发生在 eulerpublisher CI 工具链的 [Check] 测试阶段，原因是 CI runner 缺少 `shunit2` Shell 测试框架依赖，属 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境中安装 `shunit2` 测试框架（可通过包管理器如 `dnf install shunit2` 或手动放置到 `/usr/local/etc/eulerpublisher/tests/common/` 路径），或由 eulerpublisher 工具自行管理该依赖。

## 需要进一步确认的点
- `shunit2` 是 eulerpublisher CI 工具的标准依赖，还是某次 runner 环境变更导致其丢失。建议检查同批次其他 PR 的 [Check] 阶段是否也因相同原因失败——若是，则为 runner 环境全局问题。
