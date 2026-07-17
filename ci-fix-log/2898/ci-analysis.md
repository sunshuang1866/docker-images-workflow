# CI 失败分析报告

## 基本信息
- PR: #2898 — chore(go): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 测试框架缺失
- 新模式症状关键词: shunit2: No such file or directory, common_funs.sh, [Check] test failed

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
- 失败原因: CI 环境的 `[Check]` 测试阶段调用 `common_funs.sh` 脚本，该脚本在第 13 行尝试 source `shunit2` 测试框架时失败——`shunit2` 在 CI runner 上不可用（No such file or directory）。Docker 镜像构建（#7 #8 #9 #10 #11 全部 DONE）和推送（pushing manifest … done）本身均已成功完成。

### 与 PR 变更的关联
**无关**。该 PR 新增了 `Others/go/1.25.6/24.03-lts-sp4/Dockerfile`（Go 1.25.6 在 openEuler 24.03-LTS-SP4 上的镜像）及配套的 README.md、image-info.yml、meta.yml 更新。Docker build 阶段所有步骤均成功完成（#7 DONE 67.8s, #8 DONE 40.5s, #9 DONE 1.5s, #10 DONE 0.0s, #11 DONE 41.9s），镜像成功推送到 `docker.io/openeulertest/go:1.25.6-oe2403sp4-aarch64`。失败仅发生在 CI `eulerpublisher` 工具的 `[Check]` 后处理测试阶段，因 CI runner 缺少 `shunit2` shell 测试框架而导致测试脚本无法执行。

## 修复方向

### 方向 1（置信度: 高）
在 CI runner 环境上安装 `shunit2` shell 单元测试框架（例如通过 `dnf install shunit2` 或从 GitHub 下载 shUnit2 2.1.x 版本并放入 PATH），使 `/usr/local/etc/eulerpublisher/tests/container/common/common_funs.sh` 脚本能正常 source 该框架，恢复 `[Check]` 测试步骤。此修复位于 CI 基础设施层，与 PR 代码无关。

### 方向 2（置信度: 低）
若 `shunit2` 原本应当随 `eulerpublisher` 包一同安装但被遗漏，则需将 `shunit2` 添加为 `eulerpublisher` RPM 包的依赖项（`Requires: shunit2`），在包升级后重新部署 CI 环境。

## 需要进一步确认的点
- CI runner（aarch64 节点）上 `shunit2` 是否曾经可用、是否因环境更新被移除
- `eulerpublisher` 包的 RPM spec 是否遗漏了 `shunit2` 依赖声明
- 同环境下的其他镜像（如同仓库其他 Go 版本）的 `[Check]` 测试是否也因同样原因失败，以确认此为环境级问题而非单次偶发

## 修复验证要求
修复方向不涉及正则 patch 外部源文件，无需额外验证步骤。
