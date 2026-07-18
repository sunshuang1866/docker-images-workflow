# CI 失败分析报告

## 基本信息
- PR: #3153 — docs: update available base image tags in README
- 失败类型: lint-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 纯文档PR触发应用商店校验
- 新模式症状关键词: Path Error, expected path, appstore, README.md, update.py

## 根因分析

### 直接错误
```
2026-07-16 20:34:19,171 - INFO: Difference: [ "README.md" ]
2026-07-16 20:34:43,043 - INFO: Clone https://gitcode.com/sunshuang1866/****-docker-images.git successfully.
2026-07-16 20:34:43,051 - ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+-------------+-----------------------------------------------------+--------------+
| Check Items |                     Description                     | Check Result |
+-------------+-----------------------------------------------------+--------------+
|  README.md  | [Path Error] The expected path should be /README.md |   FAILURE    |
+-------------+-----------------------------------------------------+--------------+
```

### 根因定位
- 失败位置: `eulerpublisher/update/container/app/update.py:273`
- 失败原因: PR 仅修改了仓库根目录下的 `README.md` 和 `README.en.md`（纯文档更新），但 CI 的应用商店发布规范校验（appstore release specification check）对所有变更文件执行路径校验。根目录的 `README.md` 不匹配应用商店要求的路径格式（如 `{category}/{app}/{version}/{os-version}/Dockerfile` 等应用镜像子目录结构），被判定为路径错误。

### 与 PR 变更的关联
PR 变更（更新的基础镜像 tag 列表、新增 SP4/SP3/25.09 版本）本身是合法的文档内容更新，但触发 CI 失败的原因是：该 PR **仅有文档类文件变更**，却经过了应用商店发布规范校验步骤。`update.py` 将根目录 `README.md` 视为需要校验的应用商店发布文件，而其路径不符合应用镜像子目录的预期格式，导致校验失败。

## 修复方向

### 方向 1（置信度: 中）
CI 校验逻辑可能未区分"纯文档 PR"和"应用镜像发布 PR"。如果 `update.py` 或 CI 流水线配置中存在对文件变更类型的前置过滤（例如仅校验特定子目录下的文件），需要确保根目录的文档文件（`README.md`、`README.en.md`）被排除在应用商店发布规范校验之外。或者，该 PR 本不应触发应用商店校验 job。

### 方向 2（置信度: 低）
错误消息 "The expected path should be /README.md" 可能存在路径归一化问题——CI 工具内部使用无前导 `/` 的路径（如 `README.md`），而校验规则中保存的期望路径带有前导 `/`（如 `/README.md`），导致字面比较失败。但这与"该文件本不应被校验"的根因指向不同，需阅读 `update.py` 源码确认。

## 需要进一步确认的点
1. 需查阅 `eulerpublisher/update/container/app/update.py` 中第 270-280 行的校验逻辑，确认路径校验的具体匹配规则，以及是否存在文件类型/路径白名单。
2. 需确认 CI 流水线配置中"应用商店发布规范校验"job 的触发条件——是否应对所有 PR 触发（包括纯文档 PR），还是仅对包含应用镜像目录文件变更的 PR 触发。
3. 需确认该 PR 实际对应的 CI job 编号：日志中展示的 `PR 3184 [sunshuang1866:fix/3153 -> master]` 为 fix 分支创建的另一个 PR，需要确认 #3153 本身的 CI 日志是否缺失或与此一致。

## 修复验证要求
若修复方向涉及修改 `eulerpublisher/update/container/app/update.py` 中的路径校验逻辑或白名单规则，code-fixer 必须：
1. 从上游 eulerpublisher 仓库拉取 `update.py` 完整源码，确认第 222-273 行之间的路径校验函数签名和匹配逻辑。
2. 验证修改后的逻辑对纯文档 PR（仅根目录 README 文件变更）能正确跳过校验，同时对包含应用镜像目录（如 `AI/`、`Database/`）文件变更的 PR 仍正常执行校验。
