#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
智能RAG监控系统 - TermGPT记忆自动触发器
实时监控记忆文件变化，自动检测关键词并触发相关记忆注入

作者：AI助手 & 用户
版本：1.0
"""

import os
import re
import json
import time
import signal
import subprocess
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Set, Optional
import logging
from dataclasses import dataclass
from queue import Queue, Empty
import argparse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.expanduser('~/.config/ganaterm/smart_rag.log')),
        logging.StreamHandler()
    ]
)

@dataclass
class TriggerRule:
    """触发规则配置"""
    keywords: List[str]          # 关键词列表
    pattern: str                 # 正则表达式模式
    memory_types: List[str]      # 要搜索的记忆类型
    importance_threshold: float  # 重要性阈值
    cooldown_seconds: int       # 冷却时间（避免重复触发）
    max_results: int            # 最大结果数量
    category: str               # 分类标签

class SmartRAGMonitor:
    """智能RAG监控器"""
    
    def __init__(self, config_dir: str = "~/.config/ganaterm"):
        self.config_dir = Path(config_dir).expanduser()
        self.memory_dir = self.config_dir / "memory"
        self.rag_config_file = self.config_dir / "rag_config.json"
        self.rag_queue_file = self.config_dir / "rag_queue.jsonl"
        self.rag_log_file = self.config_dir / "smart_rag.log"
        
        # 运行状态
        self.running = False
        self.monitor_threads = []
        self.trigger_queue = Queue()
        
        # 触发历史（避免重复触发）
        self.trigger_history: Dict[str, datetime] = {}
        self.recent_contents: Set[str] = set()
        
        # 加载配置
        self.trigger_rules = self._load_trigger_rules()
        
        # 注册信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logging.info(f"SmartRAGMonitor 初始化完成，监控目录: {self.memory_dir}")
    
    def _load_trigger_rules(self) -> List[TriggerRule]:
        """加载触发规则配置"""
        default_rules = [
            TriggerRule(
                keywords=["错误", "error", "bug", "问题", "失败", "异常"],
                pattern=r"(?i)(错误|error|bug|问题|失败|异常|exception)",
                memory_types=["mid", "long"],
                importance_threshold=0.3,
                cooldown_seconds=60,
                max_results=3,
                category="debug"
            ),
            TriggerRule(
                keywords=["学习", "教程", "如何", "怎么", "方法"],
                pattern=r"(?i)(学习|教程|如何|怎么|方法|how to|tutorial|learn)",
                memory_types=["mid", "long"],
                importance_threshold=0.4,
                cooldown_seconds=120,
                max_results=5,
                category="learning"
            ),
            TriggerRule(
                keywords=["代码", "编程", "函数", "api", "python", "javascript"],
                pattern=r"(?i)(代码|编程|函数|api|python|javascript|code|programming)",
                memory_types=["mid", "long"],
                importance_threshold=0.5,
                cooldown_seconds=90,
                max_results=4,
                category="coding"
            ),
            TriggerRule(
                keywords=["配置", "设置", "安装", "部署", "环境"],
                pattern=r"(?i)(配置|设置|安装|部署|环境|config|setup|install|deploy)",
                memory_types=["mid", "long"],
                importance_threshold=0.6,
                cooldown_seconds=180,
                max_results=3,
                category="config"
            ),
            TriggerRule(
                keywords=["项目", "文件", "目录", "路径"],
                pattern=r"(?i)(项目|文件|目录|路径|project|file|directory|path)",
                memory_types=["short", "mid"],
                importance_threshold=0.3,
                cooldown_seconds=30,
                max_results=2,
                category="project"
            )
        ]
        
        if self.rag_config_file.exists():
            try:
                with open(self.rag_config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    rules = []
                    for rule_data in config_data.get('trigger_rules', []):
                        rules.append(TriggerRule(**rule_data))
                    if rules:
                        return rules
            except Exception as e:
                logging.warning(f"加载配置文件失败，使用默认配置: {e}")
        
        # 保存默认配置
        self._save_trigger_rules(default_rules)
        return default_rules
    
    def _save_trigger_rules(self, rules: List[TriggerRule]):
        """保存触发规则配置"""
        try:
            config_data = {
                'trigger_rules': [
                    {
                        'keywords': rule.keywords,
                        'pattern': rule.pattern,
                        'memory_types': rule.memory_types,
                        'importance_threshold': rule.importance_threshold,
                        'cooldown_seconds': rule.cooldown_seconds,
                        'max_results': rule.max_results,
                        'category': rule.category
                    }
                    for rule in rules
                ]
            }
            
            with open(self.rag_config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logging.error(f"保存配置文件失败: {e}")
    
    def _signal_handler(self, signum, frame):
        """信号处理器"""
        logging.info(f"收到信号 {signum}，正在停止监控...")
        self.stop()
    
    def start_monitoring(self):
        """开始监控"""
        if self.running:
            logging.warning("监控已在运行")
            return
            
        self.running = True
        logging.info("开始智能RAG监控...")
        
        # 启动文件监控线程
        for memory_file in ["short_term.jsonl", "mid_term.jsonl", "long_term.jsonl"]:
            file_path = self.memory_dir / memory_file
            if file_path.exists():
                thread = threading.Thread(
                    target=self._monitor_file,
                    args=(file_path, memory_file.split('_')[0]),
                    daemon=True
                )
                thread.start()
                self.monitor_threads.append(thread)
        
        # 启动触发处理线程
        processor_thread = threading.Thread(
            target=self._process_triggers,
            daemon=True
        )
        processor_thread.start()
        self.monitor_threads.append(processor_thread)
        
        logging.info(f"已启动 {len(self.monitor_threads)} 个监控线程")
    
    def stop(self):
        """停止监控"""
        self.running = False
        logging.info("正在停止所有监控线程...")
        
        # 等待线程结束
        for thread in self.monitor_threads:
            if thread.is_alive():
                thread.join(timeout=2)
        
        self.monitor_threads.clear()
        logging.info("智能RAG监控已停止")
    
    def _monitor_file(self, file_path: Path, memory_type: str):
        """监控单个记忆文件"""
        logging.info(f"开始监控文件: {file_path}")
        
        try:
            # 使用tail -f监控文件
            cmd = ["tail", "-f", str(file_path)]
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            while self.running:
                try:
                    line = process.stdout.readline()
                    if not line:
                        time.sleep(0.1)
                        continue
                    
                    line = line.strip()
                    if line:
                        self._analyze_new_content(line, memory_type)
                        
                except Exception as e:
                    logging.error(f"读取文件 {file_path} 出错: {e}")
                    break
            
            # 清理进程
            try:
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                
        except Exception as e:
            logging.error(f"监控文件 {file_path} 失败: {e}")
    
    def _analyze_new_content(self, line: str, memory_type: str):
        """分析新添加的记忆内容"""
        try:
            # 解析JSON行
            memory_data = json.loads(line)
            content = memory_data.get('content', {})
            
            if isinstance(content, dict):
                text_content = content.get('content', '')
            else:
                text_content = str(content)
            
            # 避免重复分析相同内容
            content_hash = hash(text_content)
            if content_hash in self.recent_contents:
                return
            
            self.recent_contents.add(content_hash)
            
            # 限制recent_contents大小，避免内存泄漏
            if len(self.recent_contents) > 1000:
                self.recent_contents.clear()
            
            # 检查是否匹配触发规则
            for rule in self.trigger_rules:
                if self._should_trigger(text_content, rule, memory_type):
                    trigger_info = {
                        'rule': rule,
                        'content': text_content,
                        'memory_type': memory_type,
                        'timestamp': datetime.now(),
                        'memory_data': memory_data
                    }
                    
                    self.trigger_queue.put(trigger_info)
                    logging.info(f"触发规则 {rule.category}: {text_content[:100]}...")
                    
        except json.JSONDecodeError:
            pass  # 忽略非JSON行
        except Exception as e:
            logging.error(f"分析内容失败: {e}")
    
    def _should_trigger(self, content: str, rule: TriggerRule, memory_type: str) -> bool:
        """检查是否应该触发规则"""
        # 检查记忆类型
        if memory_type not in rule.memory_types:
            return False
        
        # 检查关键词匹配
        content_lower = content.lower()
        keyword_match = any(keyword.lower() in content_lower for keyword in rule.keywords)
        
        # 检查正则表达式匹配
        pattern_match = bool(re.search(rule.pattern, content))
        
        if not (keyword_match or pattern_match):
            return False
        
        # 检查冷却时间
        rule_key = f"{rule.category}_{hash(content) % 10000}"
        now = datetime.now()
        
        if rule_key in self.trigger_history:
            last_trigger = self.trigger_history[rule_key]
            if (now - last_trigger).seconds < rule.cooldown_seconds:
                return False
        
        # 更新触发历史
        self.trigger_history[rule_key] = now
        
        # 清理旧的触发历史
        cutoff_time = now - timedelta(hours=24)
        self.trigger_history = {
            k: v for k, v in self.trigger_history.items()
            if v > cutoff_time
        }
        
        return True
    
    def _process_triggers(self):
        """处理触发队列"""
        logging.info("启动触发处理器")
        
        while self.running:
            try:
                # 从队列获取触发信息，设置超时避免阻塞
                trigger_info = self.trigger_queue.get(timeout=1.0)
                self._handle_trigger(trigger_info)
                self.trigger_queue.task_done()
                
            except Empty:
                continue
            except Exception as e:
                logging.error(f"处理触发器失败: {e}")
    
    def _handle_trigger(self, trigger_info: Dict):
        """处理单个触发事件"""
        rule = trigger_info['rule']
        content = trigger_info['content']
        memory_type = trigger_info['memory_type']
        
        try:
            # 搜索相关记忆
            related_memories = self._search_related_memories(content, rule)
            
            if related_memories:
                # 生成RAG注入信息
                rag_injection = {
                    'timestamp': trigger_info['timestamp'].isoformat(),
                    'trigger_rule': rule.category,
                    'original_content': content[:200] + '...' if len(content) > 200 else content,
                    'memory_type': memory_type,
                    'related_memories': related_memories,
                    'suggestion': self._generate_suggestion(content, related_memories, rule)
                }
                
                # 写入RAG队列文件
                self._write_rag_queue(rag_injection)
                
                logging.info(f"生成RAG注入 [{rule.category}]: 找到 {len(related_memories)} 条相关记忆")
                
        except Exception as e:
            logging.error(f"处理触发事件失败: {e}")
    
    def _search_related_memories(self, content: str, rule: TriggerRule) -> List[Dict]:
        """搜索相关记忆"""
        related_memories = []
        
        try:
            # 提取关键词进行搜索
            search_keywords = []
            
            # 从规则中提取关键词
            for keyword in rule.keywords:
                if keyword.lower() in content.lower():
                    search_keywords.append(keyword)
            
            # 从内容中提取额外关键词
            content_words = re.findall(r'\b\w{3,}\b', content.lower())
            important_words = [word for word in content_words 
                             if len(word) > 3 and word not in ['the', 'and', 'for', 'that', 'this']][:5]
            search_keywords.extend(important_words)
            
            # 搜索每种指定的记忆类型
            for mem_type in rule.memory_types:
                memory_file = self.memory_dir / f"{mem_type}_term.jsonl"
                if memory_file.exists():
                    memories = self._search_memory_file(memory_file, search_keywords, rule.importance_threshold)
                    related_memories.extend(memories)
            
            # 按重要性排序并限制数量
            related_memories.sort(key=lambda x: x.get('importance', 0), reverse=True)
            return related_memories[:rule.max_results]
            
        except Exception as e:
            logging.error(f"搜索相关记忆失败: {e}")
            return []
    
    def _search_memory_file(self, file_path: Path, keywords: List[str], threshold: float) -> List[Dict]:
        """搜索单个记忆文件"""
        matches = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        memory = json.loads(line.strip())
                        content = memory.get('content', {})
                        
                        if isinstance(content, dict):
                            text = content.get('content', '')
                        else:
                            text = str(content)
                        
                        # 检查重要性阈值
                        importance = memory.get('importance', 0)
                        if importance < threshold:
                            continue
                        
                        # 检查关键词匹配
                        text_lower = text.lower()
                        matching_keywords = [kw for kw in keywords if kw.lower() in text_lower]
                        
                        if matching_keywords:
                            memory_info = {
                                'id': memory.get('id', ''),
                                'time': memory.get('time', ''),
                                'content': text[:300] + '...' if len(text) > 300 else text,
                                'importance': importance,
                                'matching_keywords': matching_keywords,
                                'memory_type': memory.get('memory_type', file_path.stem.split('_')[0])
                            }
                            matches.append(memory_info)
                            
                    except json.JSONDecodeError:
                        continue
                        
        except Exception as e:
            logging.error(f"搜索文件 {file_path} 失败: {e}")
        
        return matches
    
    def _generate_suggestion(self, content: str, memories: List[Dict], rule: TriggerRule) -> str:
        """生成智能建议"""
        if not memories:
            return f"检测到 {rule.category} 相关内容，但未找到相关历史记忆。"
        
        suggestions = []
        
        if rule.category == "debug":
            suggestions.append("🐛 发现可能的问题，以下是相关的调试记忆：")
        elif rule.category == "learning":
            suggestions.append("📚 检测到学习需求，以下是相关的学习记忆：")
        elif rule.category == "coding":
            suggestions.append("💻 发现编程相关内容，以下是相关的代码记忆：")
        elif rule.category == "config":
            suggestions.append("⚙️ 检测到配置相关操作，以下是相关的配置记忆：")
        elif rule.category == "project":
            suggestions.append("📁 发现项目相关内容，以下是相关的项目记忆：")
        else:
            suggestions.append(f"🔍 检测到 {rule.category} 相关内容，以下是相关记忆：")
        
        for i, memory in enumerate(memories[:3], 1):
            time_str = memory.get('time', '').split('.')[0] if memory.get('time') else '未知时间'
            content_preview = memory.get('content', '')[:100]
            suggestions.append(f"{i}. [{time_str}] {content_preview}...")
        
        if len(memories) > 3:
            suggestions.append(f"还有 {len(memories) - 3} 条相关记忆...")
        
        return '\n'.join(suggestions)
    
    def _write_rag_queue(self, rag_injection: Dict):
        """写入RAG队列文件"""
        try:
            with open(self.rag_queue_file, 'a', encoding='utf-8') as f:
                json_line = json.dumps(rag_injection, ensure_ascii=False)
                f.write(json_line + '\n')
                
        except Exception as e:
            logging.error(f"写入RAG队列失败: {e}")
    
    def get_rag_queue(self, limit: int = 10) -> List[Dict]:
        """获取RAG队列中的内容"""
        if not self.rag_queue_file.exists():
            return []
        
        try:
            rag_items = []
            with open(self.rag_queue_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            # 获取最近的记录
            for line in lines[-limit:]:
                try:
                    rag_items.append(json.loads(line.strip()))
                except json.JSONDecodeError:
                    continue
            
            return rag_items
            
        except Exception as e:
            logging.error(f"读取RAG队列失败: {e}")
            return []
    
    def clear_rag_queue(self):
        """清空RAG队列"""
        try:
            if self.rag_queue_file.exists():
                self.rag_queue_file.unlink()
            logging.info("RAG队列已清空")
        except Exception as e:
            logging.error(f"清空RAG队列失败: {e}")
    
    def get_status(self) -> Dict:
        """获取监控状态"""
        return {
            'running': self.running,
            'monitor_threads': len(self.monitor_threads),
            'trigger_rules': len(self.trigger_rules),
            'trigger_history_size': len(self.trigger_history),
            'recent_contents_size': len(self.recent_contents),
            'rag_queue_size': len(self.get_rag_queue(1000)),
            'config_dir': str(self.config_dir),
            'memory_dir': str(self.memory_dir)
        }

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='智能RAG监控系统')
    parser.add_argument('action', choices=['start', 'stop', 'status', 'queue', 'clear'], 
                       help='操作类型')
    parser.add_argument('--config-dir', default='~/.config/ganaterm',
                       help='配置目录路径')
    parser.add_argument('--daemon', action='store_true',
                       help='以守护进程模式运行')
    
    args = parser.parse_args()
    
    monitor = SmartRAGMonitor(args.config_dir)
    
    if args.action == 'start':
        print("🚀 启动智能RAG监控系统...")
        monitor.start_monitoring()
        
        if args.daemon:
            print("📡 监控系统正在后台运行...")
            try:
                while True:
                    time.sleep(60)  # 每分钟检查一次
                    if not monitor.running:
                        break
            except KeyboardInterrupt:
                print("\n⏹️ 收到中断信号，正在停止...")
        else:
            print("📡 监控系统正在运行，按 Ctrl+C 停止...")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n⏹️ 正在停止监控...")
        
        monitor.stop()
        print("✅ 监控系统已停止")
        
    elif args.action == 'stop':
        print("⏹️ 停止监控...")
        monitor.stop()
        
    elif args.action == 'status':
        status = monitor.get_status()
        print("📊 监控状态:")
        for key, value in status.items():
            print(f"  {key}: {value}")
            
    elif args.action == 'queue':
        print("📋 RAG队列内容:")
        queue_items = monitor.get_rag_queue(10)
        for i, item in enumerate(queue_items, 1):
            print(f"  {i}. [{item['timestamp']}] {item['trigger_rule']}")
            print(f"     {item['suggestion']}")
            print()
            
    elif args.action == 'clear':
        monitor.clear_rag_queue()
        print("🗑️ RAG队列已清空")

if __name__ == "__main__":
    main() 