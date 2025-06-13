#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
上下文增强器 - 提供智能上下文理解和增强功能
"""

import json
import re
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

class ContextEnhancer:
    """上下文增强器，提供智能上下文理解和增强功能"""
    
    def __init__(self):
        """初始化上下文增强器"""
        self.context_window = []
        self.max_context_length = 10
        self.context_weights = {
            "recent": 1.0,
            "relevant": 0.8,
            "important": 0.6
        }
        
    def enhance_messages(self, messages: List[Dict], memory_manager: Any = None) -> List[Dict]:
        """增强消息列表的上下文
        
        Args:
            messages: 消息列表
            memory_manager: 记忆管理器实例
            
        Returns:
            增强后的消息列表
        """
        if not messages:
            return []
            
        # 更新上下文窗口
        self._update_context_window(messages)
        
        # 获取相关记忆
        relevant_memories = []
        if memory_manager:
            # 从最新消息中提取关键词
            latest_message = messages[-1]
            if isinstance(latest_message, dict) and "content" in latest_message:
                query = latest_message["content"]
                relevant_memories = memory_manager.get_context_enhanced_memories(query)
        
        # 构造增强的上下文
        enhanced_messages = []
        
        # 添加系统提示
        system_prompt = self._generate_system_prompt(relevant_memories)
        if system_prompt:
            enhanced_messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        # 添加相关记忆
        if relevant_memories:
            memory_context = self._format_memories(relevant_memories)
            enhanced_messages.append({
                "role": "system",
                "content": f"相关记忆：\n{memory_context}"
            })
        
        # 添加原始消息
        enhanced_messages.extend(messages)
        
        return enhanced_messages
    
    def _update_context_window(self, messages: List[Dict]) -> None:
        """更新上下文窗口
        
        Args:
            messages: 消息列表
        """
        # 添加新消息到上下文窗口
        self.context_window.extend(messages)
        
        # 保持窗口大小
        if len(self.context_window) > self.max_context_length:
            self.context_window = self.context_window[-self.max_context_length:]
    
    def _generate_system_prompt(self, memories: List[Dict]) -> str:
        """生成系统提示
        
        Args:
            memories: 相关记忆列表
            
        Returns:
            系统提示文本
        """
        prompt_parts = []
        
        # 添加时间信息
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        prompt_parts.append(f"当前时间：{current_time}")
        
        # 添加记忆统计
        if memories:
            memory_types = {}
            for memory in memories:
                memory_type = memory.get("memory_type", "unknown")
                memory_types[memory_type] = memory_types.get(memory_type, 0) + 1
            
            memory_stats = ", ".join([f"{k}: {v}" for k, v in memory_types.items()])
            prompt_parts.append(f"相关记忆统计：{memory_stats}")
        
        # 添加上下文信息
        if self.context_window:
            context_info = self._analyze_context()
            if context_info:
                prompt_parts.append(f"上下文分析：{context_info}")
        
        return "\n".join(prompt_parts)
    
    def _format_memories(self, memories: List[Dict]) -> str:
        """格式化记忆列表
        
        Args:
            memories: 记忆列表
            
        Returns:
            格式化后的记忆文本
        """
        formatted_memories = []
        
        for memory in memories:
            # 提取记忆内容
            content = memory.get("content", "")
            if isinstance(content, dict):
                content = content.get("content", str(content))
            
            # 获取时间信息
            time_info = memory.get("time_info", memory.get("time", "未知时间"))
            
            # 获取记忆类型
            memory_type = memory.get("memory_type", "unknown")
            
            # 格式化记忆
            formatted_memory = f"[{memory_type}] {time_info}: {content}"
            formatted_memories.append(formatted_memory)
        
        return "\n".join(formatted_memories)
    
    def _analyze_context(self) -> str:
        """分析当前上下文
        
        Returns:
            上下文分析结果
        """
        if not self.context_window:
            return ""
            
        # 统计角色分布
        role_stats = {}
        for message in self.context_window:
            role = message.get("role", "unknown")
            role_stats[role] = role_stats.get(role, 0) + 1
        
        # 分析对话主题
        topics = self._extract_topics()
        
        # 构造分析结果
        analysis = []
        
        # 添加角色统计
        role_info = ", ".join([f"{k}: {v}" for k, v in role_stats.items()])
        analysis.append(f"角色分布：{role_info}")
        
        # 添加主题信息
        if topics:
            analysis.append(f"主要主题：{', '.join(topics)}")
        
        return " | ".join(analysis)
    
    def _extract_topics(self) -> List[str]:
        """从上下文中提取主题
        
        Returns:
            主题列表
        """
        topics = set()
        
        # 常见主题关键词
        topic_keywords = {
            "代码": ["代码", "编程", "开发", "实现", "函数", "类", "模块"],
            "配置": ["配置", "设置", "环境", "参数", "选项"],
            "问题": ["问题", "错误", "异常", "bug", "故障"],
            "功能": ["功能", "特性", "能力", "支持"],
            "性能": ["性能", "速度", "效率", "优化"],
            "安全": ["安全", "权限", "认证", "加密"],
            "数据": ["数据", "存储", "数据库", "文件"],
            "网络": ["网络", "连接", "请求", "API"],
            "界面": ["界面", "UI", "交互", "显示"],
            "测试": ["测试", "验证", "检查", "调试"]
        }
        
        # 从消息中提取主题
        for message in self.context_window:
            if isinstance(message, dict) and "content" in message:
                content = message["content"].lower()
                for topic, keywords in topic_keywords.items():
                    if any(keyword in content for keyword in keywords):
                        topics.add(topic)
        
        return list(topics)
    
    def get_context_summary(self) -> str:
        """获取上下文摘要
        
        Returns:
            上下文摘要
        """
        if not self.context_window:
            return "无上下文信息"
            
        # 获取最近的对话
        recent_messages = self.context_window[-3:]
        
        # 提取主题
        topics = self._extract_topics()
        
        # 构造摘要
        summary_parts = []
        
        # 添加主题信息
        if topics:
            summary_parts.append(f"当前主题：{', '.join(topics)}")
        
        # 添加最近对话
        recent_dialog = []
        for message in recent_messages:
            role = message.get("role", "unknown")
            content = message.get("content", "")
            if isinstance(content, dict):
                content = content.get("content", str(content))
            recent_dialog.append(f"{role}: {content[:50]}...")
        
        if recent_dialog:
            summary_parts.append("最近对话：\n" + "\n".join(recent_dialog))
        
        return "\n".join(summary_parts)
    
    def clear_context(self) -> None:
        """清除上下文窗口"""
        self.context_window = []