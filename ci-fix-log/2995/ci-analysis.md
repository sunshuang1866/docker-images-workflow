# CI 失败分析报告

## 基本信息
- PR: #2995 — chore(bwa): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 测试脚本CRLF换行
- 新模式症状关键词: `/bin/sh^M`, `bad interpreter`, `No such file or directory`, `bwa_test.sh`

## 根因分析

### 直接错误
```
2026-07-10 11:58:06,454 - INFO - [Check] checking ****test/bwa:0.7.18-oe2403sp4-x86_64 ...
/bin/sh: /usr/lib64/python3.9/../../etc/eulerpublisher/tests/container/app/bwa_test.sh: /bin/sh^M: bad interpreter: No such file or directory
2026-07-10 11:58:06,457 - CRITICAL - [Check] test failed
+-------------+-------------+--------------+
| Check Items | Description | Check Result |
+-------------+-------------+--------------+
+-------------+-------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: CI 节点上 `/usr/etc/eulerpublisher/tests/container/app/bwa_test.sh`（通过 `eulerpublisher` 包安装）
- 失败原因: CI 工具 `eulerpublisher` 的 bwa 镜像测试脚本 `bwa_test.sh` 文件使用了 Windows 风格换行符（CRLF），导致 shebang 行 `#!/bin/sh\r\n` 被内核解析为解释器路径 `/bin/sh\r`（`\r` = `^M`），该路径不存在，系统报 `bad interpreter: No such file or directory`

### 与 PR 变更的关联
**无关。** PR 变更仅包含以下内容：
1. 新增 `HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile`（bwa 0.7.18 在 openEuler 24.03-LTS-SP4 上的构建文件）
2. 更新 `HPC/bwa/README.md`（追加新版本 tag 说明）
3. 更新 `HPC/bwa/doc/image-info.yml`（追加新版本行）
4. 更新 `HPC/bwa/meta.yml`（追加新版本路径映射）

Docker 镜像的构建（`#7 DONE 199.0s`）和推送（`[Push] finished`）均成功完成。失败仅发生在 CI 框架的后置 [Check] 测试阶段，原因是 CI 服务器上已安装的 `eulerpublisher` 包内的 `bwa_test.sh` 测试脚本自身存在换行符问题，与本次 PR 的 Dockerfile 或元数据修改无关。

## 修复方向

### 方向 1（置信度: 中）
CI 运维人员需要在构建节点上修复 `eulerpublisher` 包中的 `bwa_test.sh` 文件，将其从 CRLF（Windows 换行）转换为 LF（Unix 换行）。可在 CI 节点上执行 `dos2unix /usr/etc/eulerpublisher/tests/container/app/bwa_test.sh` 或等效的 `sed -i 's/\r$//'` 命令，或更新 `eulerpublisher` RPM 包修复源文件后重新发布。

## 需要进一步确认的点
1. CI 节点上 `bwa_test.sh` 的 CRLF 换行是何时引入的——是该脚本首次添加时就存在的问题，还是后续某次更新引入的。
2. 是否只有 `bwa_test.sh` 存在此问题，还是 `eulerpublisher` 包中其他测试脚本也存在同样的 CRLF 问题——`dos2unix` 或 `sed` 修复范围可能需要覆盖整个 `tests/container/app/` 目录。
3. 其他架构（如 aarch64）的 CI job 是否也因同样的 `bwa_test.sh` CRLF 问题而失败——需要获取 aarch64 job 日志确认。
4. 若 `bwa_test.sh` 的 CRLF 问题是 `eulerpublisher` RPM 包本身的缺陷，需确认 RPM 包最新版本是否已修复。
