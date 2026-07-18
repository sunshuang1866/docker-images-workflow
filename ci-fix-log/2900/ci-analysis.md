# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 模式39
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

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
- 失败位置: CI 测试框架 `common_funs.sh:13`
- 失败原因: CI 后置检查（[Check]）阶段中，测试脚本 `common_funs.sh` 尝试通过 `. shunit2` 加载 `shunit2` shell 单元测试框架，但该框架未安装在 CI runner 的环境中，导致检查步骤失败，进而整个 Pipeline 被标记为 `FAILURE`。

### 与 PR 变更的关联
**与 PR 变更无关。** Docker 镜像构建（[Build]）和推送（[Push]）阶段均成功完成：
- `#10 DONE 41.6s` — httpd 编译和 `make install` 成功
- `#11 DONE 0.1s` — 用户/组创建及配置 sed 修改成功
- `#12 DONE 0.0s` — COPY httpd-foreground 成功
- `#13 DONE 0.1s` — chmod +x 成功
- `#14 DONE 31.3s` — 镜像导出、attestation 生成、推送到 registry 均成功
- `[Build] finished` / `[Push] finished` 均正常

失败仅发生在 CI 流水线的 [Check] 后置检查阶段，根因是 CI 环境本身缺少 `shunit2` 框架，与 PR 新增的 Dockerfile、httpd-foreground 脚本、文档更新等代码变更无关。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境中安装 `shunit2` shell 测试框架。`shunit2` 是一个独立可安装的 shell 单元测试库，需确保其安装路径在 `common_funs.sh` 中引用的搜索路径（`PATH` 或特定目录）下。这是 CI 运维层面的基础设施问题，Code Fixer 无需对 PR 代码做任何修改。

## 需要进一步确认的点
- 确认 `shunit2` 在 openEuler 24.03-LTS-SP4 的 yum 源中是否可用包安装（如 `yum install shunit2`），还是需要从 GitHub 手动下载部署。
- 确认其他运行在同一 CI 环境中的镜像（如 24.03-lts-sp2 的 httpd 或其他应用镜像）是否也存在相同的 [Check] 失败，以判断这是该 runner 的孤立问题还是通用 CI 环境缺陷。
