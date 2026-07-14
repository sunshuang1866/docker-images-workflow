# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试框架缺失
- 新模式症状关键词: shunit2, file not found, common_funs.sh, eulerpublisher, Check test failed

## 根因分析

### 直接错误
```
2026-07-10 09:18:18,896 - INFO - [Check] checking ****test/httpd:2.4.66-oe2403sp4-x86_64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:18:18,902 - CRITICAL - [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI 的 check 步骤在执行时，测试框架 `common_funs.sh` 尝试通过 `. shunit2` 引入 `shunit2` shell 单元测试库失败，提示 `shunit2: file not found`，导致 `[Check] test failed`。`shunit2` 不在 CI runner 的 `$PATH` 中或未被安装。

### 与 PR 变更的关联
与 PR 改动**无关**。PR 新增的 httpd 2.4.66 on openEuler 24.03-LTS-SP4 Dockerfile 构建完全成功（所有 7 个 RUN 步骤均通过，镜像已成功构建并推送到 registry）。失败发生在 CI 自身的 `eulerpublisher` 测试基础设施中——`shunit2` 框架缺失导致 check 步骤无法执行，属 CI 基础设施问题。

Docker 构建日志显示：
- `#10 DONE 41.6s` — configure + make + make install 成功
- `#11 DONE 0.1s` — 用户创建与配置完成
- `#12 DONE 0.0s` — COPY httpd-foreground 成功
- `#13 DONE 0.1s` — chmod +x 成功
- `#14 DONE 31.3s` — 镜像导出和推送成功

Build 阶段日志中唯一的非致命信息是一条 Docker BuildKit 警告：
```
1 warning found (use docker --debug to expand):
 - LegacyKeyValueFormat: "ENV key=value" should be used instead of legacy "ENV key value" format (line 5)
```
此警告（`ENV HTTPD_PREFIX /usr/local/apache2` 应改为 `ENV HTTPD_PREFIX=/usr/local/apache2`）不导致构建失败，与 check 失败无关。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境中安装 `shunit2` 包（openEuler 下包名一般为 `shunit2`），或确保 check 步骤所在的执行环境 `$PATH` 包含 `shunit2` 可执行文件。这不是 Dockerfile 或 PR 代码的问题，需要 CI 基础设施管理员介入。

## 需要进一步确认的点
- 确认 CI runner 上是否安装了 `shunit2` 包：`rpm -qa | grep shunit2` 或 `which shunit2`
- 确认 `eulerpublisher` 版本是否有最低依赖要求声明，其中是否包含 `shunit2`
- 确认该 check 失败是否在**其他成功 PR**（如相同镜像的不同架构）中也出现——如果同样存在但被忽略，则可能是 check 步骤配置了 `|| true` 等容错逻辑，但本 PR 恰好处在边界

## 修复验证要求
无需 code-fixer 修改任何代码。此问题属于 CI 基础设施范畴，需运维人员检查 CI runner 上 `shunit2` 的安装状态。
