# CI 失败分析报告

## 基本信息
- PR: #2900 — chore(httpd): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: CI测试框架缺失shunit2
- 新模式症状关键词: shunit2: file not found, common_funs.sh, eulerpublisher, source, [Check] test failed

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
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`
- 失败原因: CI runner 上缺少 `shunit2` shell 测试框架，`common_funs.sh` 脚本在 `source shunit2` 时因找不到该文件而失败，导致整个 [Check] 阶段在未执行任何测试用例的情况下崩溃。Docker 镜像构建和推送均已完成且成功（`[Build] finished`、`[Push] finished`）。

### 与 PR 变更的关联
与 PR 变更**无关**。本次 PR 新增了 httpd 2.4.66 在 openEuler 24.03-LTS-SP4 上的 Dockerfile、httpd-foreground 启动脚本，并更新了 README.md、image-info.yml、meta.yml 元数据文件。Docker 镜像本身已成功构建并推送到注册中心（`docker.io/****test/httpd:2.4.66-oe2403sp4-x86_64`），失败仅发生在 CI 后置检查阶段，根因是 runner 环境缺少 `shunit2` 依赖，与代码变更无涉。

## 修复方向

### 方向 1（置信度: 高）
CI 管理员在 openEuler 24.03-LTS-SP4 对应的 CI runner 节点上安装 `shunit2` 包（如 `dnf install shunit2` 或从 https://github.com/kward/shunit2 手动部署），确保 `shunit2` 可执行文件在 `eulerpublisher` 测试框架的 `PATH` 中可被 source 加载。

## 需要进一步确认的点
- 确认这是否是 openEuler 24.03-LTS-SP4 CI runner 节点的普遍问题（该 runner 是否首次运行 httpd 镜像的 [Check] 测试，以及同批次其他 SP4 PR 是否也因相同原因失败）
- 确认 `shunit2` 在 openEuler 24.03-LTS-SP4 上的包名和可用性（是否为 `shunit2` 或 `shUnit2`）
- 确认 `eulerpublisher` 测试框架的依赖声明是否遗漏了 `shunit2`；若是框架缺陷，需在 `eulerpublisher` 项目侧修复
