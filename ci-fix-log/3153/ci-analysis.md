# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 模式11
- 新模式标题: (留空)
- 新模式症状关键词: (留空)

## 根因分析

### 直接错误
```
+--------------+-----------------------------------------------------+--------------+
| Check Items  |                     Description                     | Check Result |
+--------------+-----------------------------------------------------+--------------+
| README.en.md | [Path Error] The expected path should be /README.md |   FAILURE    |
|  README.md   | [Path Error] The expected path should be /README.md |   FAILURE    |
+--------------+-----------------------------------------------------+--------------+
2026-07-12 15:33:13,075-update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（appstore 发布规范预检）
- 失败原因: CI 的 appstore 发布规范检查工具对 PR 变更文件进行路径校验，将仓库根目录下的 `README.md` 和 `README.en.md` 判定为路径不符合规范，要求期望路径为 `/README.md`。该检查本应针对应用镜像目录（如 `AI/`、`Bigdata/` 等）内的文件进行校验，但被错误地应用到了纯文档类的仓库根级 README 文件上。

### 与 PR 变更的关联
PR #3153 是一个纯文档变更，仅在 `README.en.md` 和 `README.md` 中更新了可用基础镜像的 Tags 列表（新增 24.03-lts-sp4、24.03-lts-sp3、25.09 条目，调整排序）。这些文件是仓库根级的项目文档，不属于任何应用镜像目录。CI 的 appstore 发布规范检查将这两个根级 README 文件纳入了路径校验范围，而该检查设计上是为应用镜像发布服务的，根本不应审查仓库根目录下的项目文档文件。

## 修复方向

### 方向 1（置信度: 中）
CI 的 appstore 发布规范预检脚本（`eulerpublisher/update/container/app/update.py`）需要增加对仓库根级文档文件的豁免逻辑：当变更文件位于仓库根目录（即不属于任何 `{场景目录}/` 子目录）时，跳过路径校验，不再报 `[Path Error]`。例如：对 `README.md`、`README.en.md`、`LICENSE`、`CONTRIBUTING.md` 等根级项目文件不做 appstore 路径规范检查。

### 方向 2（置信度: 低）
如果 CI 检查脚本不允许豁免根级文件，可考虑将此 PR 合并方式改为手动合并（绕过 CI 的 appstore 检查），因为该 PR 仅包含文档变更，不影响任何应用镜像的构建或发布。

## 需要进一步确认的点
1. 确认 `eulerpublisher/update/container/app/update.py` 中路径校验的具体逻辑——为何 `/README.md` 路径本身会被判定为不符合期望路径 `/README.md`？需要查看 `update.py` 的路径校验函数（约 line 260-273）来理解 `Path Error` 的触发条件。
2. 确认该 CI check job 是否是所有 PR 的强制门禁，或是可以通过在 PR 中添加特定 label（如 `skip-appstore-check`）跳过。
3. 确认是否有其他纯文档类 PR 遇到相同问题，以判断这是否为已知的 CI 配置缺陷。

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
（不适用——此问题不涉及对第三方/上游源文件的正则 patch 操作。）
