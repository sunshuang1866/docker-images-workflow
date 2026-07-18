# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: CI测试框架依赖缺失
- 新模式症状关键词: shunit2: file not found, common_funs.sh, [Check] test failed

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
Notifying upstream projects of job completion
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh`:13
- 失败原因: CI Check 阶段，测试框架脚本 `common_funs.sh` 尝试通过 `. shunit2` 引入 shunit2 测试框架，但该文件在 CI runner 上不存在（`file not found`），导致所有检查项均无法执行（Check Results 表格为空），CI 判定构建失败。

### 与 PR 变更的关联

**与 PR 代码变更无关**。证据：
1. Docker 镜像构建全部 7 个步骤成功完成（`#10 DONE 41.6s`, `#11 DONE 0.1s`, `#12 DONE 0.0s`, `#13 DONE 0.1s`）。
2. 镜像推送成功（`[Push] finished`，manifest 已推送至 `docker.io/****test/httpd:2.4.66-oe2403sp4-x86_64`）。
3. 失败发生在构建和推送完成之后的 `[Check]` 阶段，根因是 CI runner 自身缺少 `shunit2` shell 测试框架，而非 PR 引入的 Dockerfile/httpd-foreground/元数据文件有任何问题。
4. PR 新增文件仅涉及 Dockerfile、httpd-foreground 入口脚本、README.md、image-info.yml、meta.yml，不含任何可能影响 CI 测试基础设施的改动。

## 修复方向

### 方向 1（置信度: 中）
CI 运维侧修复：在负责 openEuler 24.03-LTS-SP4 镜像构建的 CI runner 上安装 `shunit2` shell 测试框架，确保 `common_funs.sh` 在 Check 阶段能正确引入该依赖。

### 方向 2（置信度: 低）
如果 `shunit2` 应捆绑在 `eulerpublisher` 包内而非依赖系统安装，则需检查 `eulerpublisher` 包在 SP4 runner 上的安装完整性，确认 `shunit2` 文件是否随包正确部署到 `/usr/local/etc/eulerpublisher/tests/container/common/` 路径下。

## 需要进一步确认的点

1. **该 runner 是否为 SP4 专属 runner**：如果 openEuler 24.03-LTS-SP4 镜像的 Check 阶段使用了与 SP2/SP3 不同的 runner，需要确认该 runner 是否缺少 shunit2 而其他 runner 正常。
2. **同仓库其他 SP4 PR 是否也遇到相同问题**：例如 PR #2896（dotnet-deps 8.0/24.03-lts-sp4）等 SP4 镜像的 CI 是否也有相同的 `shunit2: file not found` 错误，以判断这是个别 runner 问题还是 SP4 全集群问题。
3. **shunit2 的预期安装路径**：需在代码库中确认 `eulerpublisher` 测试框架对 shunit2 的路径引用约定，是系统全局安装还是与 `common_funs.sh` 同目录部署。
