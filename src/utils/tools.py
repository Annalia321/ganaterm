#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
工具类 - 提供通用功能支持
"""

import os
import json
import time
import random
import string
import hashlib
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import requests
from requests.exceptions import RequestException

class Tools:
    """工具类，提供通用功能支持"""
    
    @staticmethod
    def generate_id(length: int = 8) -> str:
        """生成随机ID
        
        Args:
            length: ID长度
            
        Returns:
            随机ID字符串
        """
        chars = string.ascii_letters + string.digits
        return ''.join(random.choice(chars) for _ in range(length))
    
    @staticmethod
    def calculate_hash(content: Union[str, bytes]) -> str:
        """计算内容的哈希值
        
        Args:
            content: 要计算哈希的内容
            
        Returns:
            SHA-256哈希值
        """
        if isinstance(content, str):
            content = content.encode('utf-8')
        return hashlib.sha256(content).hexdigest()
    
    @staticmethod
    def format_timestamp(timestamp: Optional[float] = None) -> str:
        """格式化时间戳
        
        Args:
            timestamp: 时间戳，默认为当前时间
            
        Returns:
            格式化的时间字符串
        """
        if timestamp is None:
            timestamp = time.time()
        return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
    
    @staticmethod
    def safe_json_loads(text: str, default: Any = None) -> Any:
        """安全地解析JSON字符串
        
        Args:
            text: JSON字符串
            default: 解析失败时的默认值
            
        Returns:
            解析结果或默认值
        """
        try:
            return json.loads(text)
        except (json.JSONDecodeError, TypeError):
            return default
    
    @staticmethod
    def safe_json_dumps(obj: Any, ensure_ascii: bool = False) -> str:
        """安全地将对象转换为JSON字符串
        
        Args:
            obj: 要转换的对象
            ensure_ascii: 是否确保ASCII编码
            
        Returns:
            JSON字符串
        """
        try:
            return json.dumps(obj, ensure_ascii=ensure_ascii)
        except (TypeError, ValueError):
            return str(obj)
    
    @staticmethod
    def ensure_dir(directory: str) -> None:
        """确保目录存在
        
        Args:
            directory: 目录路径
        """
        if not os.path.exists(directory):
            os.makedirs(directory)
    
    @staticmethod
    def read_file(file_path: str, encoding: str = 'utf-8') -> Optional[str]:
        """读取文件内容
        
        Args:
            file_path: 文件路径
            encoding: 文件编码
            
        Returns:
            文件内容，如果失败则返回None
        """
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except Exception as e:
            print(f"读取文件出错: {e}")
            return None
    
    @staticmethod
    def write_file(file_path: str, content: str, encoding: str = 'utf-8') -> bool:
        """写入文件内容
        
        Args:
            file_path: 文件路径
            content: 要写入的内容
            encoding: 文件编码
            
        Returns:
            是否成功写入
        """
        try:
            with open(file_path, 'w', encoding=encoding) as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"写入文件出错: {e}")
            return False
    
    @staticmethod
    def append_file(file_path: str, content: str, encoding: str = 'utf-8') -> bool:
        """追加文件内容
        
        Args:
            file_path: 文件路径
            content: 要追加的内容
            encoding: 文件编码
            
        Returns:
            是否成功追加
        """
        try:
            with open(file_path, 'a', encoding=encoding) as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"追加文件出错: {e}")
            return False
    
    @staticmethod
    def make_request(url: str, method: str = 'GET', **kwargs) -> Optional[Dict]:
        """发送HTTP请求
        
        Args:
            url: 请求URL
            method: 请求方法
            **kwargs: 请求参数
            
        Returns:
            响应数据，如果失败则返回None
        """
        try:
            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            print(f"请求出错: {e}")
            return None
    
    @staticmethod
    def retry_on_failure(func: callable, max_retries: int = 3, delay: float = 1.0) -> Any:
        """失败重试装饰器
        
        Args:
            func: 要重试的函数
            max_retries: 最大重试次数
            delay: 重试延迟（秒）
            
        Returns:
            函数执行结果
        """
        def wrapper(*args, **kwargs):
            for i in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if i == max_retries - 1:
                        raise e
                    time.sleep(delay * (i + 1))
            return None
        return wrapper
    
    @staticmethod
    def format_size(size: int) -> str:
        """格式化文件大小
        
        Args:
            size: 文件大小（字节）
            
        Returns:
            格式化后的大小字符串
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.2f}{unit}"
            size /= 1024
        return f"{size:.2f}PB"
    
    @staticmethod
    def get_file_info(file_path: str) -> Dict[str, Any]:
        """获取文件信息
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件信息字典
        """
        try:
            stat = os.stat(file_path)
            return {
                "size": Tools.format_size(stat.st_size),
                "created": Tools.format_timestamp(stat.st_ctime),
                "modified": Tools.format_timestamp(stat.st_mtime),
                "accessed": Tools.format_timestamp(stat.st_atime)
            }
        except Exception as e:
            print(f"获取文件信息出错: {e}")
            return {}
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """检查URL是否有效
        
        Args:
            url: 要检查的URL
            
        Returns:
            URL是否有效
        """
        try:
            result = requests.head(url, timeout=5)
            return result.status_code < 400
        except RequestException:
            return False
    
    @staticmethod
    def extract_urls(text: str) -> List[str]:
        """从文本中提取URL
        
        Args:
            text: 要提取URL的文本
            
        Returns:
            URL列表
        """
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        return re.findall(url_pattern, text)
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """清理文件名
        
        Args:
            filename: 原始文件名
            
        Returns:
            清理后的文件名
        """
        # 移除非法字符
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        # 移除首尾空白
        filename = filename.strip()
        # 如果文件名为空，使用默认名称
        if not filename:
            filename = f"file_{Tools.generate_id()}"
        return filename
    
    @staticmethod
    def get_file_extension(filename: str) -> str:
        """获取文件扩展名
        
        Args:
            filename: 文件名
            
        Returns:
            文件扩展名（小写）
        """
        return os.path.splitext(filename)[1].lower()
    
    @staticmethod
    def is_binary_file(file_path: str) -> bool:
        """检查文件是否为二进制文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否为二进制文件
        """
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                return b'\0' in chunk
        except Exception:
            return False
    
    @staticmethod
    def get_mime_type(file_path: str) -> str:
        """获取文件的MIME类型
        
        Args:
            file_path: 文件路径
            
        Returns:
            MIME类型
        """
        import mimetypes
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type or 'application/octet-stream'
    
    @staticmethod
    def compress_text(text: str) -> str:
        """压缩文本
        
        Args:
            text: 要压缩的文本
            
        Returns:
            压缩后的文本
        """
        # 移除多余空白
        text = re.sub(r'\s+', ' ', text)
        # 移除HTML标签
        text = re.sub(r'<[^>]+>', '', text)
        # 移除特殊字符
        text = re.sub(r'[^\w\s\u4e00-\u9fff]', '', text)
        return text.strip()
    
    @staticmethod
    def extract_keywords(text: str, top_n: int = 5) -> List[str]:
        """提取文本关键词
        
        Args:
            text: 要提取关键词的文本
            top_n: 返回的关键词数量
            
        Returns:
            关键词列表
        """
        try:
            import jieba.analyse
            return jieba.analyse.extract_tags(text, topK=top_n)
        except ImportError:
            # 如果没有jieba，使用简单的词频统计
            words = text.split()
            word_freq = {}
            for word in words:
                if len(word) > 1:  # 忽略单字词
                    word_freq[word] = word_freq.get(word, 0) + 1
            return sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:top_n]
    
    @staticmethod
    def calculate_similarity(text1: str, text2: str) -> float:
        """计算两段文本的相似度
        
        Args:
            text1: 第一段文本
            text2: 第二段文本
            
        Returns:
            相似度分数，范围[0,1]
        """
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
            
            vectorizer = TfidfVectorizer()
            tfidf_matrix = vectorizer.fit_transform([text1, text2])
            return cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        except ImportError:
            # 如果没有sklearn，使用简单的字符重叠率
            set1 = set(text1)
            set2 = set(text2)
            intersection = set1.intersection(set2)
            union = set1.union(set2)
            return len(intersection) / len(union) if union else 0 