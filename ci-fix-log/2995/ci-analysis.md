# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本换行符错误
- 新模式症状关键词: bad interpreter, ^M, CRLF, bwa_test.sh, eulerpublisher

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: `/usr/etc/eulerpublisher/tests/container/app/bwa_test.sh`（eulerpublisher CI 工具包内的测试脚本）
- 失败原因: CI 基础设施中 eulerpublisher 包自带的 `bwa_test.sh` 测试脚本包含 Windows 风格换行符（CRLF，由错误信息中的 `^M` 证实），导致内核将 shebang 行 `#!/bin/sh\r` 中的 `\r` 视为解释器名称的一部分，找不到 `/bin/sh\r` 这个解释器而执行失败。

### 与 PR 变更的关联
**无关。** PR 仅新增了以下内容，不涉及任何测试脚本或 CI 配置：
- `HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile`（新增 Dockerfile）
- `HPC/bwa/README.md`（新增 tag 说明）
- `HPC/bwa/doc/image-info.yml`（新增 tag metadata）
- `HPC/bwa/meta.yml`（新增 path 映射）

Docker 镜像构建（`[Build] finished`）和推送（`[Push] finished`）两步均已成功完成。失败仅发生在 eulerpublisher 测试框架的 `[Check]` 阶段，属于 CI 工具自身问题。

## 修复方向

### 方向 1（置信度: 高）
eulerpublisher 包中的 `bwa_test.sh` 文件被以 CRLF 换行符写入或传输到 CI runner 上。需要修复 eulerpublisher 包的打包/部署流程，确保该测试脚本使用 LF 换行符。若能直接访问 CI runner，可临时执行 `dos2unix` 或 `sed -i 's/\r$//'` 修复该文件。但根本修复应在 eulerpublisher 源码仓库中将该文件转为 LF 格式后重新发布包。

## 需要进一步确认的点
- `bwa_test.sh` 在 eulerpublisher 源码仓库中是否本身即为 CRLF 格式（通过 `file` 命令或 `cat -A` 检查）
- 若源码中为 LF，打包/发布流程中哪一步引入了 CRLF 转换（如 git clone 时 core.autocrlf 设置、打包脚本、文件传输方式等）
- 同包的其它测试脚本（如其他应用的 `*_test.sh`）是否也存在同样问题
