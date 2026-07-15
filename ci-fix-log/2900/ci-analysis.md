# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式（参考：模式39「CI工具依赖缺失」）
- 新模式标题: shunit2测试框架缺失
- 新模式症状关键词: shunit2: file not found, common_funs.sh, eulerpublisher

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: .: shunit2: file not found
2026-07-10 09:18:18,902-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh`:13
- 失败原因: CI 环境的 [Check] 阶段运行 `eulerpublisher` 测试框架时，`common_funs.sh` 脚本尝试 source `shunit2`（Shell 单元测试框架），但该测试框架未安装在该 CI runner 上。Docker 镜像的构建和推送均已成功完成（`[Build] finished` / `[Push] finished`），仅 [Check] 阶段因 CI 工具链不完整而失败。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 提交了 httpd 2.4.66 在 openEuler 24.03-LTS-SP4 上的 Dockerfile、启动脚本及配套元数据文件。Docker 镜像构建成功（10/10 步骤均 DONE），镜像已成功推送到测试仓库 `docker.io/****test/httpd:2.4.66-oe2403sp4-x86_64`。失败发生在构建完成后的 CI 后处理/测试阶段，由 runner 环境缺少 `shunit2` 库引起，与 PR 代码变更无关。

## 修复方向

### 方向 1（置信度: 高）
CI runner 环境缺少 `shunit2` shell 测试框架，需要 CI 管理员在构建节点上安装 `shunit2` 包，或在 `eulerpublisher` 的测试依赖中声明 `shunit2` 并确保其可用。

### 方向 2（置信度: 低）
如果 `shunit2` 应在当前 CI 镜像中以文件形式预置（而非通过包管理器安装），则需检查 CI 镜像构建流程是否遗漏了 `shunit2` 的部署步骤。

## 需要进一步确认的点
1. `shunit2` 在 CI 环境中的预期安装方式（RPM 包 `shunit2` 安装，还是手动部署到 `/usr/local/etc/eulerpublisher/tests/container/common/` 目录下）。
2. 该 `shunit2: file not found` 错误是否在该 CI runner 上是首次出现（即是否为新引入的 CI 环境问题），还是该 runner 本身长期缺少 `shunit2`。
3. 同类 SP4 的其他 PR（如可对比的已有成功 PR）的 [Check] 阶段是否也遇到过相同错误。

## 修复验证要求
此失败为 infra-error，无需 code-fixer 对 Dockerfile 或元数据文件做任何修改。如 CI 管理员确认 `shunit2` 问题已修复后，建议触发 CI 重跑进行验证。
