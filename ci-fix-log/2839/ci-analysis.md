# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试框架缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, Check test failed

## 根因分析

### 直接错误
```
2026-07-09 09:40:24,013 - INFO - [Check] checking ****test/postgres:17.6-oe2403sp4-x86_64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 09:40:24,021 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh`:13
- 失败原因: CI Runner 上缺少 `shunit2` Bash 单元测试框架，导致 `eulerpublisher` 的 [Check] 阶段（镜像功能验证测试）在执行测试脚本时无法找到 `shunit2` 依赖而失败。

### 与 PR 变更的关联
**与 PR 变更无关。** 此次 PR 仅新增了以下文件：
- `Database/postgres/17.6/24.03-lts-sp4/Dockerfile` — PostgreSQL 17.6 构建文件
- `Database/postgres/17.6/24.03-lts-sp4/entrypoint.sh` — 容器入口脚本
- 更新 `Database/postgres/README.md` 和 `Database/postgres/meta.yml`

Docker 镜像的构建和推送阶段均**全部成功**（日志显示 `#8 DONE 268.4s`、`[Build] finished`、`[Push] finished`），PostgreSQL 源码编译安装步骤全部正常完成。失败发生在镜像构建完成后的 [Check] 测试阶段，是 CI 基础设施（测试框架依赖）问题，与 PR 的 Dockerfile 或 entrypoint.sh 内容无关。

## 修复方向

### 方向 1（置信度: 高）
在 CI Runner 上安装 `shunit2` Bash 测试框架。`shunit2` 是一个标准的 shell 单元测试库，通常可通过以下方式之一获取：
- 从 EPEL/系统仓库安装（如 `yum install shunit2`）
- 从 GitHub releases 下载到 `/usr/local/bin/` 或 CI 脚本的 `PATH` 路径中

这是 CI 基础设施维护问题，**Code Fixer 无需处理**，应由 CI 运维团队在 runner 镜像中预装 `shunit2`。

## 需要进一步确认的点
1. 确认 `shunit2` 在 openEuler 24.03-LTS-SP4 仓库中的包名（可能是 `shunit2` 或 `shUnit2`）
2. 确认该 CI Runner 是否是为此 PR 新分配的 runner（如果是存量 runner，需确认为何 `shunit2` 丢失）
3. 确认其他同时期的 PR 是否也遇到了同样的 [Check] 阶段失败，以判断是单点问题还是全局 CI 环境退化

## 修复验证要求
（不适用——本问题为 infra-error，不涉及代码修改或正则 patch）
