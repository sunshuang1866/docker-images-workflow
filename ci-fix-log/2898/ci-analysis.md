# CI 失败分析报告

## 基本信息
- PR: #2898 — chore(go): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: shunit2缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh

## 根因分析

### 直接错误
```
2026-07-09 12:32:51,073 - INFO - [Check] checking openeulertest/go:1.25.6-oe2403sp4-aarch64 ...
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 12:32:51,082 - CRITICAL - [Check] test failed
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh:13`
- 失败原因: CI 宿主环境的测试框架脚本 `common_funs.sh` 第 13 行尝试加载 `shunit2`（shell 单元测试框架），但 `shunit2` 未安装在 CI runner 的 PATH 中，导致 Check 阶段无法执行任何测试即告失败。

### 与 PR 变更的关联
**无关**。PR 变更仅包含 4 个文件：
1. 新增 `Others/go/1.25.6/24.03-lts-sp4/Dockerfile` — Go 1.25.6 在 openEuler 24.03-LTS-SP4 上的新 Dockerfile
2. `Others/go/README.md` — 文档中添加新 tag 行
3. `Others/go/doc/image-info.yml` — 元数据中添加新 tag 行
4. `Others/go/meta.yml` — 添加新的构建条目 `1.25.6-oe2403sp4`

Docker 构建阶段（Build + Push）完全成功，镜像已构建并推送至 `openeulertest/go:1.25.6-oe2403sp4-aarch64`。失败发生在 CI 流水线的 Check（测试验证）阶段，原因是 CI runner 环境缺少 `shunit2` 测试依赖，与 PR 代码变更无任何关联。

## 修复方向

### 方向 1（置信度: 高）
CI 运维人员需在 aarch64 构建节点（以及可能涉及的 x86_64 节点）上安装 `shunit2` 包。该包是 openEuler 容器镜像 CI 测试框架（`eulerpublisher`）的运行时依赖，缺失会导致所有镜像的 Check 阶段失败。在 CI runner 上执行 `dnf install shunit2 -y` 或等效命令即可修复。

### 方向 2（置信度: 低，排除性方向）
如果 `shunit2` 已正确安装但 Check 脚本仍找不到，则需检查：
- `shunit2` 的安装路径是否在 PATH 中
- `common_funs.sh` 中加载 `shunit2` 的路径引用是否正确（硬编码路径 vs PATH 查找）

## 需要进一步确认的点
1. 同一 PR 的 x86_64 构建 job 是否也因同样的 `shunit2` 缺失而失败？（当前日志仅包含 aarch64 的 Check 阶段输出）
2. `shunit2` 是否在 CI runner 镜像/节点上计划安装而未安装，还是节点配置遗漏？
3. 确认 aarch64 CI runner 节点的实际环境中是否存在 `/usr/bin/shunit2` 或类似路径

## 修复验证要求
无需 code-fixer 介入。此为 CI 基础设施问题，需 CI 运维在 runner 环境层面修复。
