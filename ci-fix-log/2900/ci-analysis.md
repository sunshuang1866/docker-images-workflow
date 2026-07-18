# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试框架缺失
- 新模式症状关键词: shunit2, file not found, common_funs.sh, [Check] test failed

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
- 失败位置: CI runner 环境 `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 流水线的 [Check] 测试阶段依赖 `shunit2`（Shell 单元测试框架），但该框架未安装在 CI runner 上，导致 `common_funs.sh` 第 13 行的 `. shunit2` source 命令失败，测试空跑退出

### 与 PR 变更的关联
**与 PR 变更无关**。Docker 镜像的构建和推送均已成功完成：
- `#10 DONE 41.6s` — httpd 编译安装成功
- `#11 DONE 0.1s` — groupadd/useradd 和配置修改成功
- `#14 DONE 31.3s` — 镜像导出和推送成功
- `[Build] finished`、`[Push] finished`

失败仅发生在构建推送完成后的容器验证 [Check] 阶段，该阶段因 CI runner 环境中缺少 `shunit2` 测试框架而无法执行任何测试用例（Check Items 表格为空）。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境中安装 `shunit2` 测试框架。`shunit2` 是一个标准的 Shell 单元测试库，可通过以下方式安装：
- **安装**: `dnf install shunit2` 或 `apt-get install shunit2`（取决于 runner OS）
- **验证**: 安装后确认 `/usr/share/shunit2/shunit2` 或 `/usr/local/share/shunit2/shunit2` 可被 source

若无法直接安装系统包，也可将 `shunit2` 脚本下载到 CI 测试脚本的搜索路径中。

## 需要进一步确认的点
- CI runner 当前的操作系统版本和包管理器类型（以确定 `shunit2` 的正确安装命令）
- 是否所有 CI runner（x86_64、aarch64）都缺少 `shunit2`，还是仅特定架构的 runner 存在此问题
- `common_funs.sh` 中 `shunit2` 的预期 source 路径，以确认安装后是否需要调整环境变量
