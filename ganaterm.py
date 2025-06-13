#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Ganaterm - 智能终端AI助手
"""

import os
import sys
import signal
from typing import Optional, List, Dict, Any, Union

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

# 导入管理器
from core.config_manager import ConfigManager
from core.model_manager import ModelManager
from core.command_handler import CommandHandler
from memory.memory_manager import MemoryManager
from utils.logger import Logger
from utils.ui_manager import UIManager
from utils.tools import Tools

class Ganaterm:
    """Ganaterm主程序"""
    
    def __init__(self):
        """初始化Ganaterm"""
        # 初始化工具类
        self.tools = Tools()
        
        # 初始化配置管理器
        self.config_manager = ConfigManager()
        
        # 初始化日志管理器
        self.logger = Logger(self.config_manager)
        
        # 初始化UI管理器
        self.ui_manager = UIManager(self.config_manager, self.logger)
        
        # 初始化模型管理器
        self.model_manager = ModelManager(self.config_manager, self.logger)
        
        # 初始化记忆管理器
        self.memory_manager = MemoryManager(self.config_manager, self.logger)
        
        # 初始化命令处理器
        self.command_handler = CommandHandler(
            self.config_manager,
            self.logger,
            self.model_manager,
            self.memory_manager,
            self.ui_manager
        )
        
        # 注册信号处理
        self._register_signals()
    
    def _register_signals(self) -> None:
        """注册信号处理"""
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)
    
    def _handle_signal(self, signum: int, frame: Any) -> None:
        """处理信号
        
        Args:
            signum: 信号编号
            frame: 当前帧
        """
        self.logger.info(f"收到信号: {signum}")
        self.cleanup()
        sys.exit(0)
    
    def cleanup(self) -> None:
        """清理资源"""
        try:
            # 保存配置
            self.config_manager.save_config()
            
            # 保存记忆
            self.memory_manager.save_memories()
            
            # 记录日志
            self.logger.info("程序正常退出")
            
        except Exception as e:
            self.logger.error("清理资源失败", exc_info=True)
    
    def run(self) -> None:
        """运行程序"""
        try:
            # 显示欢迎信息
            self.ui_manager.print_welcome()
            
            # 检查模型可用性
            availability = self.model_manager.check_model_availability()
            for model, status in availability.items():
                self.ui_manager.print_model_status(model, status)
            
            # 主循环
            while True:
                try:
                    # 获取用户输入
                    command = self.ui_manager.get_input()
                    
                    # 处理命令
                    if not self.command_handler.handle_command(command):
                        break
                    
                except KeyboardInterrupt:
                    self.logger.info("收到中断信号")
                    break
                    
                except Exception as e:
                    self.logger.error("处理命令失败", exc_info=True)
                    self.ui_manager.print_error(f"处理命令失败: {str(e)}")
            
        except Exception as e:
            self.logger.error("程序运行失败", exc_info=True)
            self.ui_manager.print_error(f"程序运行失败: {str(e)}")
            
    finally:
            self.cleanup()

def main():
    """主函数"""
    # 创建程序实例
    app = Ganaterm()
    
    # 运行程序
    app.run()

if __name__ == "__main__":
    main()
