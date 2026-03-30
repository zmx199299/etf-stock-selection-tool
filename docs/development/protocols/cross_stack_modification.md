# 跨栈联动修改与冷备份协议 (Cross-Stack Modification Protocol)

## 目的
当需求涉及“前端UI + Rust中间层 + Python核心引擎”的前后中跨栈联动修改（如：修改核心配置的数据结构、调整算法逻辑）时，为了防止代码改“炸”导致整个系统瘫痪，必须采取先冷备份、后TDD修改、再更新文档的标准操作流程。

## 标准操作流程 (SOP)

### 第一步：创建本地冷备份 (Cold Backup)
在修改任何代码之前，必须先将当前正常工作的目标代码目录打包成 `.tar.gz` 文件，存放在项目根目录的 `backups/` 文件夹下。
> **注意**：`backups/` 目录已被加入 `.gitignore`，这些冷备份文件**不参与 Git 版本管理**，完全是本地安全底线。

命令示例：
```bash
tar -czvf backups/src-python_pre_feature_$(date +%Y%m%d%H%M%S).tar.gz src-python/
```

### 第二步：测试驱动开发 (TDD) 修改后端代码
1. 首先修改对应的单元测试文件（如 `test_calculator.py`, `test_config.py`）。
2. 运行测试确保其失败 (RED 阶段)。
3. 修改对应的 Python/Rust 源代码。
4. 运行测试直到其全部通过 (GREEN 阶段)。
5. 运行全量集成测试，确保本次修改没有破坏其他模块。

### 第三步：修改前端交互 (Frontend UI)
根据后端修改的结构，调整 Vue 页面的展示与交互逻辑（如 `Config.vue`）。运行 `npm run dev` 在本地确认视觉效果无误。

### 第四步：同步更新开发文档
所有修改完成后，必须同步将改动（如配置字典的结构变化、新的参数等）更新到：
- `docs/development/human/` 对应阶段的文档
- `docs/development/ai/` 对应阶段的文档

## 恢复方案 (Rollback)
如果修改失败或陷入无法解决的报错，直接删除被破坏的文件夹，然后解压冷备份文件恢复原状：
```bash
rm -rf src-python/
tar -xzvf backups/src-python_pre_feature_xxx.tar.gz
```
