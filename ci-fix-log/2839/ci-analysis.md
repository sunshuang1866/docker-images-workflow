# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式（与模式39"CI工具依赖缺失"同类但症状不同）
- 新模式标题: Check测试框架缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, eulerpublisher Check

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 09:40:24,021-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-09 09:40:24,021 - CRITICAL - [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `eulerpublisher` CI 编排工具测试脚本 `common_funs.sh:13`（`[Check]` 阶段）
- 失败原因: CI runner 环境中 `shunit2` 测试框架文件不存在，`common_funs.sh` 在第 13 行尝试引入 `shunit2` 时失败，导致所有镜像功能验证用例无法加载和执行，`[Check]` 阶段返回 CRITICAL 并标记构建失败。检查结果表为空（行数 0），进一步确认没有任何测试用例被执行。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了 PostgreSQL 17.6 在 openEuler 24.03-LTS-SP4 上的支持文件（Dockerfile、entrypoint.sh、README.md 更新、meta.yml 更新）。Docker 镜像的构建和推送阶段均成功完成：

- `#8 DONE 268.4s` — `make && make install` 编译安装完整通过，PostgreSQL 所有组件（bin、pl、test/regress 等）均安装至 `/usr/local/pgsql/`
- `#9 DONE 0.1s` — entrypoint.sh COPY 成功
- `#10 DONE 0.1s` — chmod 成功
- `#11 DONE 58.0s` — 镜像导出、manifest 生成、推送到 registry 全部完成
- `[Build] finished` + `[Push] finished` 日志已输出

失败仅发生在 `eulerpublisher` 的 `[Check]` 后构建检测阶段，属于 CI 基础设施层面的 `shunit2` 依赖缺失，不影响镜像构建正确性。

## 修复方向

### 方向 1（置信度: 高）
CI runner 环境缺少 `shunit2` 测试框架。需运维人员在 CI runner 镜像或初始化脚本中补充安装 `shunit2`（通常为 shell 测试框架，可通过 `dnf install shunit2` 或从 GitHub 拉取安装）。Code Fixer 无需处理此问题。

### 方向 2（可选）
若短期内无法修复 runner 环境，可考虑在 `common_funs.sh` 中添加容错逻辑：当 `shunit2` 缺失时跳过测试而非报 CRITICAL，避免误拦正常的镜像构建 PR。

## 需要进一步确认的点
1. `shunit2` 是否为该 CI runner 环境的标准预装组件 — 若同仓库其他镜像 PR 的 [Check] 阶段同样失败，则可确认为 CI 环境整体问题
2. 该 runner 是临时分配的还是固定环境 — 若为临时分配，可能是镜像模板变更导致 `shunit2` 遗漏
3. 上次成功的 postgres 镜像 PR（如 `17.6-oe2403sp2`）在构建时 [Check] 阶段是否正常通过，以确认 `shunit2` 是否为近期丢失
