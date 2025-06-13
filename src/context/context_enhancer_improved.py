#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
改进版上下文增强器 - 提供更智能的记忆检索和上下文扩充
"""

import re
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

class ImprovedContextEnhancer:
    def __init__(self, memory_manager, system_prompt):
        """初始化上下文增强器
        
        Args:
            memory_manager: 记忆管理器实例
            system_prompt: 系统提示
        """
        self.memory_manager = memory_manager
        self.system_prompt = system_prompt
        
    def enhance_messages(self, messages, max_tokens=800):
        """增强消息上下文，添加相关记忆
        
        Args:
            messages: 消息历史记录
            max_tokens: 最大上下文增强token数
            
        Returns:
            增强后的消息列表
        """
        # 1. 提取用户最新查询
        if len(messages) < 2 or "content" not in messages[-1]:
            return messages
        
        # 获取用户最新查询
        latest_query = messages[-1]["content"]
        
        # 获取当前时间（这是正确的、真实的时间！）
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 2. 获取最近几条记忆（短期记忆摘要）
        recent_memories = self.memory_manager.get_recent_memories(3)
        recent_memory_summary = "【过去对话记录】\n"
        if recent_memories:
            for mem in recent_memories:
                time_str = mem.get("time", "").split(".")[0]
                content = self._extract_memory_content(mem)
                content_type = "user" if "用户" in content else "assistant" if "助手" in content else "system"
                role = "用户" if content_type == "user" else "助手" if content_type == "assistant" else "系统"
                recent_memory_summary += f"[历史时间 {time_str}] {role}: {content[:100]}\n"
        else:
            recent_memory_summary += "没有最近对话记录\n"
        
        # 3. 触发RAG获取相关记忆
        try:
            context_memories = self.memory_manager.get_context_enhanced_memories(latest_query, 5)
            rag_memory_text = "【相关记忆】\n"
            if context_memories:
                for mem in context_memories:
                    time_str = mem.get("time", "").split(".")[0]
                    content = self._extract_memory_content(mem)
                    content_type = "user" if "用户" in content else "assistant" if "助手" in content else "system"
                    role = "用户" if content_type == "user" else "助手" if content_type == "assistant" else "系统"
                    rag_memory_text += f"[历史时间 {time_str}] {role}: {content[:150]}\n"
            else:
                rag_memory_text += "未找到相关记忆\n"
        except Exception as e:
            rag_memory_text = f"【无法获取相关记忆: {str(e)}】\n"
        
        # 4. 构建增强上下文，特别强调当前时间
        enhanced_context = (
            f"⚠️⚠️⚠️ 【系统信息】当前真实时间是: {current_time} ⚠️⚠️⚠️\n\n"
            f"{recent_memory_summary}\n\n"
            f"{rag_memory_text}\n\n"
            f"⚠️ 重要提示：你必须使用当前真实时间 {current_time}，忽略所有历史对话中提到的时间。\n"
            f"在回复中自然地引用当前时间({current_time})，不要使用历史对话中的旧时间。"
        )
        
        # 5. 创建增强后的消息列表
        enhanced_messages = messages.copy()
        
        # 在系统消息后插入增强上下文
        for i, msg in enumerate(enhanced_messages):
            if msg["role"] == "system":
                # 将增强上下文附加到系统消息
                enhanced_messages[i]["content"] = f"{msg['content']}\n\n{enhanced_context}"
                break
        
        return enhanced_messages
    
    def _extract_memory_content(self, memory):
        """从记忆对象中提取内容文本
        
        Args:
            memory: 记忆对象
            
        Returns:
            内容文本
        """
        content = memory.get("content", {})
        
        if isinstance(content, dict):
            if "content" in content:
                return content["content"]
            elif "text" in content:
                return content["text"]
            else:
                return str(content)
        elif isinstance(content, str):
            return content
        else:
            return str(content)
    
    def detect_file_request(self, query):
        """检测用户查询是否请求文件
        
        Args:
            query: 用户查询
            
        Returns:
            文件路径或None
        """
        # 检测文件路径模式
        file_patterns = [
            r'查看文件\s*[\'"](.*?)[\'"]',
            r'打开文件\s*[\'"](.*?)[\'"]',
            r'读取文件\s*[\'"](.*?)[\'"]',
            r'文件\s*[\'"](.*?)[\'"]的内容',
            r'(?:读取|查看|打开)\s*(~/[^\s]+)',
            r'(?:读取|查看|打开)\s*(/[^\s]+)',
            r'(?:读取|查看|打开)\s*(\./[^\s]+)',
            r'(?:读取|查看|打开)\s*([\w\.-]+\.[a-zA-Z0-9]+)'
        ]
        
        for pattern in file_patterns:
            match = re.search(pattern, query)
            if match:
                file_path = match.group(1)
                # 展开路径中的波浪线
                if file_path.startswith('~'):
                    file_path = os.path.expanduser(file_path)
                return file_path
        
        return None
    
    def enhance(self, user_query, max_memories=3):
        """获取增强的上下文
        
        Args:
            user_query: 用户查询
            max_memories: 最大记忆数量
            
        Returns:
            增强的上下文字符串
        """
        enhanced_context = ""
        
        # 检查是否有文件请求
        file_path = self.detect_file_request(user_query)
        if file_path and os.path.exists(file_path):
            try:
                # 将文件添加到记忆系统并获取内容
                if hasattr(self.memory_manager, 'add_file_to_memory'):
                    self.memory_manager.add_file_to_memory(file_path)
                    enhanced_context += f"已添加文件: {file_path}\n\n"
            except Exception as e:
                enhanced_context += f"添加文件失败: {str(e)}\n\n"
        
        # 获取相关记忆
        try:
            memories = self.memory_manager.get_context_enhanced_memories(user_query, max_memories)
            if memories:
                enhanced_context += "相关记忆:\n"
                for memory in memories:
                    content = self._extract_memory_content(memory)
                    time_str = memory.get("time", "").split(".")[0]
                    enhanced_context += f"[{time_str}] {content[:200]}...\n\n"
        except Exception as e:
            enhanced_context += f"获取记忆失败: {str(e)}\n\n"
        
        return enhanced_context.strip()
