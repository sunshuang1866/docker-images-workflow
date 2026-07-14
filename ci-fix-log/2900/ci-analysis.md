# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试框架依赖缺失
- 新模式症状关键词: shunit2, file not found, common_funs.sh

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:18:18,902-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-10 09:18:18,902 - CRITICAL - [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI Runner 的测试框架路径 `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`
- 失败原因: CI 测试框架 `eulerpublisher` 在执行 [Check] 阶段时，`common_funs.sh` 第 13 行以 `. shunit2` 方式尝试加载 `shunit2` shell 单元测试框架，但该框架未安装在 CI runner 上（file not found），导致 Check 阶段直接崩溃，测试表格为空（无任何检查项被执行）。

### 与 PR 变更的关联
**与 PR 无关。** PR 新增的 Dockerfile 构建和镜像推送均已成功完成：

- `#10 DONE 41.6s` — httpd 2.4.66 源码编译安装成功
- `#11 DONE 0.1s` — groupadd/useradd 及配置文件 sed 修改成功
- `#12 DONE 0.0s` — COPY httpd-foreground 成功
- `#13 DONE 0.1s` — chmod 成功
- `#14 exporting to image ... DONE` — 镜像导出成功
- `[Build] finished` / `[Push] finished` — 构建和推送均正常完成
- 镜像已成功推送到 `docker.io/****test/httpd:2.4.66-oe2403sp4-x86_64`

失败仅发生在构建完成后的 CI 内部 [Check] 测试阶段，与 Dockerfile 内容、meta.yml 配置、README.md 文档修改等所有 PR 变更均无关联。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 上安装 `shunit2` shell 测试框架。`shunit2` 是一个标准的 shell 单元测试库，可通过系统包管理器安装（如 `dnf install shunit2`）或从 GitHub 获取并放置到 CI runner 的 PATH 可寻路径下。

### 方向 2（置信度: 低）
如果 `shunit2` 已安装在某个非标准路径，检查 CI runner 上的 `PATH` 环境变量或 `common_funs.sh` 中加载 `shunit2` 的路径是否正确。

## 需要进一步确认的点
1. CI runner 上是否已安装 `shunit2`？执行 `which shunit2` 或 `rpm -qa | grep shunit2` 确认。
2. 其他 PR 在当前 CI 环境中是否也出现同样的 `shunit2: file not found` 错误（确认是否为全局性 infra 故障）。
3. `common_funs.sh` 中加载 `shunit2` 的路径写法是否依赖某个特定的工作目录或环境变量（如 `SHUNIT2_HOME`）。
