# CI 失败分析报告

## 基本信息
- PR: #2757 — 【自动升级】neo4j容器镜像升级至2026.05.0版本.
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: Spotless scalafmt路径修正不完整
- 新模式症状关键词: spotless, scalafmt3.conf, public/build-resources, neo4j-cypher-config, Unable to locate file

## 根因分析

### 直接错误
```
[ERROR] Failed to execute goal com.diffplug.spotless:spotless-maven-plugin:3.0.0:check (default) on project neo4j-cypher-config: Execution default of goal com.diffplug.spotless:spotless-maven-plugin:3.0.0:check failed: Unable to locate file with path: /neo4j/public/build-resources/scalafmt3.conf: Could not find resource '/neo4j/public/build-resources/scalafmt3.conf'. -> [Help 1]
```

### 根因定位
- 失败位置: `community/cypher/cypher-config/pom.xml`（neo4j-cypher-config 模块）
- 失败原因: neo4j 2026.05.0 上游将 `scalafmt3.conf` 从 `public/build-resources/scalafmt3.conf` 迁移到了 `build-resources/scalafmt3.conf`。Dockerfile 中的 `sed` 命令仅修正了 `community/cypher/front-end/cypher-macros-scala3/pom.xml` 中的引用，但 `neo4j-cypher-config` 模块（以及可能的其他模块）内的 spotless 配置仍然引用了旧路径 `public/build-resources/scalafmt3.conf`，导致 spotless-maven-plugin:check 因找不到文件而失败。

### 与 PR 变更的关联
PR 新增了 neo4j 2026.05.0 的 Dockerfile。Dockerfile 中已包含针对 `cypher-macros-scala3/pom.xml` 的 `sed` 修正（可能继承自 2026.04.0 版本的已知修复），但 neo4j 2026.05.0 上游在更多模块中引入了该路径引用，单一的 sed 命令覆盖不足，直接导致构建失败。

## 修复方向

### 方向 1（置信度: 高）
将 Dockerfile 中的 `sed` 命令从针对单个文件的修正扩展为全局修正：使用 `find` + `sed` 或 `sed` 通配路径，将**所有** pom.xml（或至少包含 `neo4j-cypher-config` 模块的 pom.xml）中 `public/build-resources/scalafmt3.conf` 的引用替换为 `build-resources/scalafmt3.conf`。需注意不要误改与 scalafmt3.conf 无关的路径。

### 方向 2（置信度: 中）
如果上游的父级 POM（如 root pom.xml 或 community/cypher/pom.xml）通过 `<scalafmt>` 或 `<spotless>` 插件集中配置了 scalafmt3.conf 路径，则仅需修正该父级 POM 中的引用即可全局生效，避免逐个模块修正。

## 需要进一步确认的点
- neo4j 2026.05.0 上游仓库中，究竟有多少个 pom.xml 或 spotless 配置文件引用了 `public/build-resources/scalafmt3.conf`（确认修正范围）
- 该引用是分散在多个子模块 pom.xml 中，还是集中在某个父级 POM 或共享配置中（影响修正策略）
- `cypher-macros-scala3/pom.xml` 中的 sed 修正是否在 2026.04.0 的 Dockerfile 中同样存在（对比验证上游变更范围）

## 修复验证要求
code-fixer 必须从 neo4j 2026.05.0 的上游源码中，用 `grep -r "public/build-resources/scalafmt3.conf"` 确认所有引用该路径的文件，验证新的 sed 命令确实能覆盖全部引用点后再提交。
