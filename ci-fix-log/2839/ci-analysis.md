# CI 失败分析报告

## 基本信息
- PR: #2839 — chore(postgres): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: shunit2测试框架缺失
- 新模式症状关键词: shunit2, No such file or directory, common_funs.sh, eulerpublisher, Check test failed

## 根因分析

### 直接错误
```
/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh: line 13: shunit2: No such file or directory
2026-07-09 09:40:24,021-/usr/local/lib/python3.11/site-packages/eulerpublisher/container/app/app.py[line:173]-CRITICAL: [Check] test failed
```

### 根因定位
- 失败位置: `/usr/local/etc/eulerpublisher/tests/container/app/../common/common_funs.sh:13`（CI 测试框架脚本）
- 失败原因: CI 编排工具 `eulerpublisher` 在执行 [Check] 阶段的镜像验证测试时，`common_funs.sh` 尝试引用 `shunit2` shell 单元测试框架，但 `shunit2` 未安装在当前 CI runner 环境中，导致测试脚本执行失败。

### 与 PR 变更的关联
PR 变更仅新增了 postgres 17.6 在 openEuler 24.03-LTS-SP4 上的 Dockerfile、entrypoint.sh 及对应元数据（README.md、meta.yml）。Docker 镜像的构建（Build）和推送（Push）阶段均已成功完成：
- `#8 DONE 268.4s`（`./configure && make -j $(nproc) && make install` 全部通过）
- `#11 DONE 58.0s`（镜像推送成功）
- `[Build] finished` / `[Push] finished`

失败仅发生在 CI 自身工具链的 [Check] 测试阶段，与 PR 代码变更**无关**。

## 修复方向

### 方向 1（置信度: 中）
在 CI runner 环境中安装 `shunit2` shell 测试框架（通过 `yum install shunit2` 或 `dnf install shunit2`），使 `eulerpublisher` 的镜像验证测试脚本 `common_funs.sh` 能够正常引用该依赖。此修复应由 CI 运维人员完成，Code Fixer 无需处理。

## 需要进一步确认的点
1. 同一 CI runner 上其他镜像（如同仓库中 postgres 17.0、17.5 等已有版本）的 [Check] 阶段是否也因 `shunit2` 缺失而失败？若其他镜像通过检查，则需确认是否使用了不同的 runner 或不同的 `eulerpublisher` 版本。
2. `shunit2` 是否需要在 `eulerpublisher` 的安装依赖中声明但遗漏了（即 `eulerpublisher` 的 `setup.py`/`setup.cfg` 中缺少此依赖声明）？
3. 若 `shunit2` 期望由 PR 提交的 Dockerfile 中安装（作为镜像测试的前置条件），需确认 `eulerpublisher` 的测试架构设计——测试脚本是在宿主机运行还是容器内运行。当前错误路径 `/usr/local/etc/eulerpublisher/` 表明脚本运行在 CI 宿主机上。
