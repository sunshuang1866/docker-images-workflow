# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试框架缺失shunit2
- 新模式症状关键词: shunit2: file not found, common_funs.sh, CRITICAL: test failed

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
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI [Check] 阶段 — `common_funs.sh:13`（source 引入 shunit2 测试框架失败）
- 失败原因: CI runner 上缺少 `shunit2` shell 测试框架库，导致测试脚本无法启动。Docker 镜像构建（#10 DONE）、推送（#14 DONE）均成功完成（日志显示 `[Build] finished`、`[Push] finished`），失败仅发生在后续的容器镜像检查/测试阶段。

### 与 PR 变更的关联
**无关。** PR 变更内容为：
- 新增 `Others/httpd/2.4.66/24.03-lts-sp4/Dockerfile`（44行，openEuler 24.03-LTS-SP4 上编译安装 httpd 2.4.66）
- 新增 `Others/httpd/2.4.66/24.03-lts-sp4/httpd-foreground`（启动脚本）
- 更新 `README.md`、`image-info.yml`、`meta.yml` 添加新镜像标签

Docker 构建阶段完全成功，httpd 源码在 `openEuler/openeuler:24.03-lts-sp4` 基础镜像上通过 `./configure && make && make install` 完成编译和安装，镜像成功推送到远程仓库。`shunit2` 缺失是 CI runner 自身环境问题，与 PR 的 Dockerfile 或任何代码变更无关。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 上安装 `shunit2` shell 测试框架。`shunit2` 是开源的 POSIX shell 单元测试库，可通过包管理器（如 `dnf install shunit2` 或 `pip install shunit2`）或手动下载安装到 `/usr/local/etc/eulerpublisher/tests/` 的预期路径下。此修复无需对 PR 代码做任何变更。

## 需要进一步确认的点
1. `shunit2` 是 CI runner 的长期依赖还是近期新增的依赖？如果是新增依赖但未在所有 runner 上安装，可能影响其他 PR 的 [Check] 阶段。
2. 其他同类 PR（如近期提交的其他 openEuler 24.03-LTS-SP4 镜像）是否也遇到相同的 `shunit2: file not found` 错误，以确认这是全局性问题而非偶然。
3. CI runner 的镜像/容器中 `shunit2` 的预期安装路径与 `common_funs.sh` 中 source 路径是否一致。
