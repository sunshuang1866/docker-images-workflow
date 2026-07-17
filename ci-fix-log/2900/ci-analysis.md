# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2测试框架缺失
- 新模式症状关键词: shunit2, file not found, common_funs.sh, [Check] test failed

## 根因分析

### 直接错误
```
[Check] checking ****test/httpd:2.4.66-oe2403sp4-x86_64 ...
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
- 失败位置: CI 运行时的 [Check] 阶段，`eulerpublisher` 测试框架文件 `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`
- 失败原因: CI 测试框架的 `common_funs.sh` 脚本在第 13 行尝试 `source shunit2` 时，`shunit2` shell 单元测试框架未安装或不在 `PATH` 中，导致所有容器检查项无法执行（Check Items 表格为空），测试阶段立即失败。

### 与 PR 变更的关联
**与 PR 变更无关。** Docker 镜像构建（步骤 #9-#14）和推送均已成功完成：
- `#10 DONE 41.6s` — configure + make + make install 全部通过
- `#11 DONE 0.1s` — groupadd/useradd/sed 配置修改成功
- `#12 DONE 0.0s` — COPY httpd-foreground 成功
- `#13 DONE 0.1s` — chmod 成功
- `#14 DONE 31.3s` — 镜像导出并推送成功
- `[Build] finished`、`[Push] finished` 均已确认

PR 仅新增了 Dockerfile、httpd-foreground 启动脚本，以及更新了 README.md、image-info.yml、meta.yml 等元数据文件，不涉及 CI 基础设施配置变更。`shunit2` 缺失是 CI runner 环境问题，与本次代码变更无关。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境中安装 `shunit2` shell 单元测试框架。`shunit2` 可从 GitHub（`kward/shunit2`）获取，应部署到 `/usr/local/etc/eulerpublisher/tests/container/common/` 目录下或确保在 `PATH` 中可被 `common_funs.sh` 正确引用。此为纯粹的 CI 基础设施维护操作，不涉及 PR 代码修改。

## 需要进一步确认的点
- 确认 CI runner（x86_64 构建节点）上 `shunit2` 是否曾在其他 PR 中正常可用——若其他 PR 的 [Check] 阶段也出现同样错误，则可确认是 runner 环境整体缺失；若仅本次出现，需检查是否因 runner 环境变更导致。
- 确认 CI 测试框架中 `common_funs.sh` 对 `shunit2` 的引用路径（相对路径 vs PATH 依赖），以选择正确的安装/部署方式。
- Dockerfile 中新增文件（Dockerfile、httpd-foreground）缺少 Copyright + SPDX-License-Identifier 头（参考模式17）；Dockerfile 第 5 行 `ENV HTTPD_PREFIX /usr/local/apache2` 使用旧式 `ENV key value` 格式，产生 `LegacyKeyValueFormat` 警告。这些问题虽非本次失败根因，但修复 infra 后可能在后续检查阶段暴露，建议一并修复。
