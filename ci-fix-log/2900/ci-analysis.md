# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试框架缺失
- 新模式症状关键词: shunit2: file not found, common_funs.sh, eulerpublisher

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
- 失败位置: CI runner 上的 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 测试 runner 缺少 `shunit2` 测试框架，导致 `[Check]` 阶段的测试脚本无法执行，所有检查项均未运行（Check Results 表为空），最终标记构建失败。

### 与 PR 变更的关联
**与 PR 变更无关**。PR 仅新增了 httpd 2.4.66 在 openEuler 24.03-LTS-SP4 上的 Dockerfile、启动脚本及配套元数据文件（meta.yml、image-info.yml、README.md）。Docker 镜像构建和推送均成功完成：

- `#7 DONE`（make install 完成，耗时 41.6s）
- `#11 DONE`（groupadd/useradd/sed 配置完成）
- `#12 DONE`（COPY httpd-foreground）
- `#13 DONE`（chmod +x）
- `#14 DONE`（exporting to image + pushing layers，推送成功）
- 日志明确显示 `[Build] finished` 和 `[Push] finished`

失败发生在构建/推送之后的 `[Check]` 阶段，错误来自 CI runner 自身的测试基础设施（`eulerpublisher/tests/`），与 Dockerfile 内容无关。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 上安装 `shunit2` 测试框架。该框架缺失导致所有镜像的 `[Check]` 阶段均无法运行测试。检查 CI runner 的测试依赖安装脚本，确认 `shunit2` 是否在预期路径中（如 `/usr/local/etc/eulerpublisher/tests/common/` 或系统 `$PATH` 下），必要时重新安装或恢复该依赖。

## 需要进一步确认的点
1. 确认 CI runner 上 `shunit2` 是否曾经存在、是否被意外清理或升级导致丢失。
2. 确认最近是否还有其他 PR 在同一 runner 上遇到相同的 `shunit2: file not found` 错误，以判断这是单次偶发问题还是持续性基础设施退化。
3. 确认 `eulerpublisher` 测试框架对 `shunit2` 的安装路径约定——是否需要将 `shunit2` 放置在 `/usr/local/etc/eulerpublisher/tests/common/` 目录下。

## 修复验证要求
无需 code-fixer 参与。此为 CI 基础设施问题，需运维人员检查并修复 CI runner 的测试依赖。
