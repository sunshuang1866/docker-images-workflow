# 修复摘要

## 修复的问题
`spotless-maven-plugin:check` 因找不到 `public/build-resources/scalafmt3.conf` 而构建失败——上游 neo4j 2026.05.0 将该文件从 `public/build-resources/` 迁移至 `build-resources/`，原 Dockerfile 的 `sed` 仅修正了 `cypher-macros-scala3/pom.xml`，未覆盖 `neo4j-cypher-config/pom.xml` 等其他包含相同引用的模块。

## 修改的文件
- `Database/neo4j/2026.05.0/24.03-lts-sp3/Dockerfile`: 将 `sed` 从单文件修正扩展为 `find . -name "pom.xml" -exec sed ... {} +`，覆盖所有 pom.xml 文件中的旧路径引用

## 修复逻辑
原 Dockerfile 第 18-19 行仅对 `community/cypher/front-end/cypher-macros-scala3/pom.xml` 执行路径替换。CI 分析报告指出 `neo4j-cypher-config` 模块（`community/cypher/cypher-config/pom.xml`）也引用了 `public/build-resources/scalafmt3.conf`，导致 spotless 检查失败。

已从上游 `neo4j/neo4j` tag `2026.05.0` 获取 `cypher-config/pom.xml` 和 `cypher-macros-scala3/pom.xml` 验证，两个文件中均包含 `<file>${maven.multiModuleProjectDirectory}/public/build-resources/scalafmt3.conf</file>`，正则匹配成功。改用 `find -name "pom.xml" -exec sed` 可确保所有子模块的 pom.xml 都被修正，不再遗漏。

## 潜在风险
- `find` 命令会遍历整个 neo4j 源码树，如果存在与 scalafmt3 无关的其他 pom.xml 文件恰好包含字符串 `public/build-resources/scalafmt3.conf`（极不可能），也会被替换，但该替换是等价的路径修正，不会引入新问题。
- 如果上游未来新增了使用其他文件名（非 pom.xml）引用此路径的配置文件，`find -name "pom.xml"` 可能遗漏。但目前从上游源码确认，该引用仅存在于 pom.xml 文件中。