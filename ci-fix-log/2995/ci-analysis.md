# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF换行
- 新模式症状关键词: bad interpreter, ^M, No such file or directory, bwa_test.sh

## 根因分析

### 直接错误
```
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457-/usr/local/lib/python3.9/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
```

### 根因定位
- 失败位置: `/usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh`（CI 测试基础设施脚本，非 PR 变更内容）
- 失败原因: `eulerpublisher` 内置的 `bwa_test.sh` 测试脚本使用了 Windows 风格换行符（CRLF），导致 shebang 行 `#!/bin/sh` 末尾附加了回车符 `\r`，内核将解释器路径解析为 `/bin/sh^M`，该路径不存在，脚本无法执行。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了 bwa 在 openEuler 24.03-lts-sp4 上的 Dockerfile 及配套元数据（README.md、image-info.yml、meta.yml）。Docker 镜像构建和推送均已成功完成：
- bwa 源码编译通过（日志 `#7 197.9`：`gcc ... -o bwa ...`），仅有编译器 warning（`-Wunused-but-set-variable`），不影响构建。
- 镜像构建完成并推送至 registry（日志 `#8`：`pushing manifest for docker.io/****test/bwa:0.7.18-oe2403sp4-x86_64`）。
- 失败发生在 CI 的 `[Check]` 阶段，由 `eulerpublisher` 工具内置的测试脚本 `bwa_test.sh` 本身的格式问题（CRLF）导致，属 CI 基础设施缺陷。

## 修复方向

### 方向 1（置信度: 高）
修复 `eulerpublisher` 包中的 `tests/container/app/bwa_test.sh` 文件，将 CRLF 换行符转换为 LF（Unix 风格）。可通过 `dos2unix` 或 `sed -i 's/\r$//'` 完成。此修改需在 `eulerpublisher` 仓库中进行，非本 PR 仓库范围。

### 方向 2（置信度: 低）
若无法直接修改 `eulerpublisher` 包的测试脚本，可在 CI 流水线的 `[Check]` 阶段执行前，对测试脚本做一次 `dos2unix` 预处理作为临时 workaround。但此方案属于治标不治本。

## 需要进一步确认的点
- `bwa_test.sh` 是近期新增的还是长期存在的脚本——如果是近期随 `eulerpublisher` 更新引入，则需要定位到具体的引入 commit。
- 确认 `eulerpublisher` 仓库中是否还有其他测试脚本也存在 CRLF 问题。
- 确认 aarch64 runner 上的对应 job 是否也因同一原因失败（日志中仅显示了 x86-64 的构建）。
