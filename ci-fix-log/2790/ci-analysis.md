# CI 失败分析报告

## 基本信息
- PR: #2790 — update readme.md
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: README路径格式校验误报
- 新模式症状关键词: Path Error, expected path should be, update.py, appstore, README.md

## 根因分析

### 直接错误
```
2026-07-14 15:28:07,685-.../eulerpublisher/update/container/app/update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`（CI appstore 发布规范预检脚本）
- 失败原因: CI 的 appstore 发布规范检查工具对根目录 `README.md` 执行了路径格式校验，报告 `[Path Error] The expected path should be /README.md`。该 PR 仅修改了 README.md 和 README.en.md 的文档内容（更新镜像版本标签列表），未新增任何应用镜像、Dockerfile 或元数据文件，不应触发 appstore 发布规范检查。

### 与 PR 变更的关联
- PR 仅修改了 `README.md` 和 `README.en.md`（两处均为纯文档变更：更新支持的镜像 Tags 列表，将 `24.03-lts-sp2` 更新为 `24.03-lts-sp3`，新增 `25.09`、`24.03-lts-sp3`、`24.03-lts-sp2` 条目）。
- 未改动任何 Dockerfile、meta.yml、image-info.yml、image-list.yml 或应用镜像相关文件。
- CI appstore 发布规范检查将根目录 `README.md` 纳入了校验范围，且因路径格式不匹配（缺少前导 `/`）导致校验失败。该失败与 PR 的文档修改内容本身无关，而是 CI 工具对非应用镜像文件执行了不应执行的规范校验。

## 修复方向

### 方向 1（置信度: 中）
CI 触发条件或 `eulerpublisher` appstore 规范检查的过滤逻辑可能存在缺陷——对仅修改根目录 README 文件的 PR 也触发了应用镜像发布规范校验。需在 CI 流水线层（Jenkins pipeline）或 `update.py` 中增加文件变更过滤：当 PR 仅涉及根目录 README.md / README.en.md 等纯文档文件、且未涉及任何应用镜像目录时，跳过 appstore 发布规范检查。

### 方向 2（置信度: 低）
`eulerpublisher/update/container/app/update.py` 中的路径规范化逻辑可能存在问题——`git diff --name-only` 输出的路径不包含前导 `/`（如 `README.md`），而校验逻辑期望带前导 `/` 的格式（如 `/README.md`）。如果方向 1 不可行，可在此处增加路径规范化处理。

## 需要进一步确认的点
1. 确认 CI 触发条件是否正确——当前 PR 仅修改根目录 README 文件，是否应触发 x86-64 架构的 appstore 发布规范检查 job。
2. 查看 `eulerpublisher/update/container/app/update.py:273` 附近的校验逻辑，确认其文件变更过滤条件是否过宽。
3. 查看 `Difference` 列表为何仅包含 `README.md` 而不包含 `README.en.md`——是否因 diff 解析逻辑只识别了单个文件。
4. 确认 `[Path Error] The expected path should be /README.md` 中的前导 `/` 要求是硬性规范还是工具 bug。

## 修复验证要求
若修复方向涉及正则 patch `eulerpublisher` 源码文件，code-fixer 需从 CI 日志记录的 `eulerpublisher` 仓库获取 `update/container/app/update.py` 的实际代码（约第 273 行及附近校验逻辑），验证路径过滤逻辑或路径格式化逻辑的修改能正确处理根目录 README 文件变更的场景后再提交。
