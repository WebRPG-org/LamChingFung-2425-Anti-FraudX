# ✅ 已完成：plugins.js 已删除

## 📋 已完成的操作

1. ✅ 已备份原有的 `plugins.js` 文件
2. ✅ 已删除 `plugins.js` 文件，强制 RPG Maker 重新扫描

## 🎯 下一步操作（重要！）

### 第 1 步：完全关闭 RPG Maker MV

**重要**: 请确保 **完全关闭** RPG Maker MV 编辑器，包括：
- 关闭所有打开的窗口（Plugin Manager、Map Editor 等）
- 关闭主编辑器窗口
- 确认任务管理器中没有 RPG Maker 进程

### 第 2 步：重新打开项目

1. 重新启动 RPG Maker MV
2. 打开您的项目：`RPG_platform/RPG_Project`
3. RPG Maker 会自动：
   - 扫描 `js/plugins/` 目录中的所有插件文件
   - 重新生成 `plugins.js` 文件
   - 识别所有新插件

### 第 3 步：验证插件是否可见

1. 在编辑器中，打开 **Tools** → **Plugin Manager**
2. 您应该能看到以下 **新插件**：

   ✅ **SimulationTraining**
      - 描述: 防詐騙模擬訓練系統 - 使用 simulation_routes.py API
      - 状态: OFF（需要手动启用）

   ✅ **SimulationTraining_Compatible** ⭐ **推荐使用**
      - 描述: 防詐騙模擬訓練系統 - 完全兼容原有RotatingScamSystem設置
      - 状态: OFF（需要手动启用）
      - **此版本完全兼容原有的 NPC 设置和路径**

   ✅ **SimulationTraining_WithNPC**
      - 描述: 防詐騙模擬訓練系統 - 帶NPC自動移動功能
      - 状态: OFF（需要手动启用）

### 第 4 步：启用插件

在 Plugin Manager 中：

1. **如果要使用兼容原有设置的版本**（推荐）：
   - 找到 `SimulationTraining_Compatible`
   - 将状态从 OFF 改为 ON
   - 点击 OK 保存

2. **如果要使用纯训练版本**（不需要 NPC）：
   - 找到 `SimulationTraining`
   - 将状态从 OFF 改为 ON
   - 点击 OK 保存

3. **如果要使用带新 NPC 配置的版本**：
   - 找到 `SimulationTraining_WithNPC`
   - 将状态从 OFF 改为 ON
   - 配置 NPC（需要使用插件命令）
   - 点击 OK 保存

## ⚠️ 重要提示

### 插件冲突

**不要同时启用多个训练插件！** 请只启用以下其中一个：
- SimulationTraining（纯训练）
- SimulationTraining_Compatible（兼容版，推荐） ⭐
- SimulationTraining_WithNPC（新 NPC 配置）

同时，如果启用了新插件，可能需要 **禁用** 旧的 `RotatingScamSystem` 插件以避免冲突。

### 插件顺序

确保新插件在插件列表中的顺序合理：
1. Community_Basic
2. MadeWithMv
3. AI_Bridge
4. AntiFraudGame
5. **SimulationTraining_Compatible** ← 新插件
6. 其他插件...

## 🎮 测试插件

启用插件后，测试功能：

### 测试 SimulationTraining_Compatible：

1. 进入游戏测试模式（F5 或 Test Play）
2. 打开控制台（F8）
3. 输入插件命令：
   ```
   StartCompatibleTraining
   ```
4. 系统会自动：
   - 移动到第一个 NPC
   - 启动模拟对话
   - 显示实时信任度和得分
   - 自动循环所有 6 个 NPC

### 测试 SimulationTraining：

1. 进入游戏测试模式
2. 打开控制台
3. 输入命令：
   ```
   StartAutoTraining 5 demo
   ```
4. 系统会启动 5 轮自动训练

## 📊 预期结果

成功后，您应该看到：
- ✅ Plugin Manager 中显示 3 个新插件
- ✅ 能够启用/禁用插件
- ✅ 能够配置插件参数（如 API_URL）
- ✅ 插件命令可以正常执行
- ✅ 游戏测试模式中能看到训练效果

## 🆘 如果仍然有问题

1. **检查插件文件完整性**：
   ```powershell
   Get-ChildItem "RPG_platform\RPG_Project\js\plugins\Simulation*.js" | Select-Object Name, Length
   ```

2. **查看 RPG Maker 错误日志**：
   - 在测试模式下按 F8 打开控制台
   - 查看是否有错误信息

3. **手动验证 plugins.js**：
   - 重启 RPG Maker 后，检查 `js/plugins.js` 是否已重新生成
   - 文件应该包含所有插件的配置

4. **联系支持**：
   - 提供截图或错误信息
   - 说明使用的 RPG Maker 版本

## 🎉 完成后

插件成功启用后，请参考以下文档：
- `RPG_Maker_兼容版本_使用指南.md` - SimulationTraining_Compatible 使用指南
- `RPG_Maker_新訓練系統使用指南.md` - SimulationTraining 使用指南  
- `RPG_Maker_NPC自動訓練_使用指南.md` - SimulationTraining_WithNPC 使用指南

祝您使用愉快！🚀

