"""引用管理器

管理搜索结果的引用、来源验证和引用格式化
"""

import hashlib
import re
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, asdict
from datetime import datetime
from urllib.parse import urlparse

from .search_tools import SearchResult


@dataclass
class Reference:
    """引用数据类"""
    id: str
    title: str
    url: str
    snippet: str
    source: str
    timestamp: datetime
    relevance_score: float
    credibility_score: float
    citation_format: str
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_search_result(cls, search_result: SearchResult, relevance_score: float = 0.0) -> 'Reference':
        """从搜索结果创建引用"""
        ref_id = hashlib.md5(search_result.url.encode()).hexdigest()[:8]
        
        return cls(
            id=ref_id,
            title=search_result.title,
            url=search_result.url,
            snippet=search_result.snippet,
            source=search_result.source,
            timestamp=search_result.timestamp or datetime.now(),
            relevance_score=relevance_score,
            credibility_score=0.0,  # 将由可信度评估器计算
            citation_format=""
        )


@dataclass
class CitationStyle:
    """引用样式"""
    name: str
    template: str
    url_format: str
    
    def format_citation(self, reference: Reference) -> str:
        """格式化引用"""
        return self.template.format(
            title=reference.title,
            url=reference.url,
            source=reference.source,
            timestamp=reference.timestamp.strftime("%Y-%m-%d")
        )


class CredibilityEvaluator:
    """可信度评估器"""
    
    def __init__(self):
        # 可信域名列表
        self.trusted_domains = {
            'wikipedia.org': 0.9,
            'gov.cn': 0.95,
            'edu.cn': 0.9,
            'ac.cn': 0.9,
            'nature.com': 0.95,
            'science.org': 0.95,
            'ieee.org': 0.9,
            'acm.org': 0.9,
            'springer.com': 0.85,
            'elsevier.com': 0.85,
            'arxiv.org': 0.8,
            'researchgate.net': 0.75,
            'scholar.google.com': 0.8,
            'pubmed.ncbi.nlm.nih.gov': 0.9,
            'who.int': 0.95,
            'un.org': 0.9,
            'worldbank.org': 0.9,
            'imf.org': 0.9
        }
        
        # 可疑域名模式
        self.suspicious_patterns = [
            r'.*\.tk$',
            r'.*\.ml$',
            r'.*\.ga$',
            r'.*\.cf$',
            r'.*blog.*',
            r'.*forum.*',
            r'.*bbs.*'
        ]
    
    def evaluate_credibility(self, reference: Reference) -> float:
        """评估引用的可信度"""
        score = 0.5  # 基础分数
        
        # 域名可信度
        domain = urlparse(reference.url).netloc.lower()
        
        # 检查可信域名
        for trusted_domain, trust_score in self.trusted_domains.items():
            if trusted_domain in domain:
                score = max(score, trust_score)
                break
        
        # 检查可疑模式
        for pattern in self.suspicious_patterns:
            if re.match(pattern, domain):
                score *= 0.5
                break
        
        # HTTPS 加分
        if reference.url.startswith('https://'):
            score += 0.1
        
        # 标题质量评估
        title_score = self._evaluate_title_quality(reference.title)
        score = (score + title_score) / 2
        
        # 内容质量评估
        content_score = self._evaluate_content_quality(reference.snippet)
        score = (score + content_score) / 2
        
        return min(1.0, max(0.0, score))
    
    def _evaluate_title_quality(self, title: str) -> float:
        """评估标题质量"""
        if not title:
            return 0.0
        
        score = 0.5
        
        # 长度适中
        if 10 <= len(title) <= 100:
            score += 0.2
        
        # 包含数字（可能是统计数据）
        if re.search(r'\d+', title):
            score += 0.1
        
        # 避免全大写
        if not title.isupper():
            score += 0.1
        
        # 避免过多标点符号
        punct_ratio = len(re.findall(r'[!?.,;:]', title)) / len(title)
        if punct_ratio < 0.2:
            score += 0.1
        
        return min(1.0, score)
    
    def _evaluate_content_quality(self, content: str) -> float:
        """评估内容质量"""
        if not content:
            return 0.0
        
        score = 0.5
        
        # 长度适中
        if 50 <= len(content) <= 500:
            score += 0.2
        
        # 句子结构
        sentences = re.split(r'[.!?]', content)
        if len(sentences) >= 2:
            score += 0.1
        
        # 避免重复内容
        words = content.lower().split()
        unique_words = set(words)
        if len(unique_words) / len(words) > 0.7:
            score += 0.1
        
        # 包含具体信息（数字、日期等）
        if re.search(r'\d{4}|\d+%|\d+\.\d+', content):
            score += 0.1
        
        return min(1.0, score)


class ReferenceManager:
    """引用管理器
    
    管理搜索结果的引用、来源验证和引用格式化
    """
    
    def __init__(self):
        self.references: Dict[str, Reference] = {}
        self.credibility_evaluator = CredibilityEvaluator()
        
        # 预定义引用样式
        self.citation_styles = {
            'apa': CitationStyle(
                name='APA',
                template='{title}. Retrieved from {url}',
                url_format='[{title}]({url})'
            ),
            'mla': CitationStyle(
                name='MLA',
                template='"{title}." Web. {timestamp}. <{url}>',
                url_format='[{title}]({url})'
            ),
            'chicago': CitationStyle(
                name='Chicago',
                template='{title}. Accessed {timestamp}. {url}',
                url_format='[{title}]({url})'
            ),
            'markdown': CitationStyle(
                name='Markdown',
                template='[{title}]({url})',
                url_format='[{title}]({url})'
            )
        }
        
        self.default_style = 'markdown'
    
    def add_search_results(self, search_results: List[SearchResult], query: str = "") -> List[Reference]:
        """添加搜索结果并转换为引用"""
        references = []
        
        for result in search_results:
            # 计算相关性分数
            relevance_score = self._calculate_relevance(result, query)
            
            # 创建引用
            reference = Reference.from_search_result(result, relevance_score)
            
            # 评估可信度
            reference.credibility_score = self.credibility_evaluator.evaluate_credibility(reference)
            
            # 生成引用格式
            reference.citation_format = self._format_citation(reference)
            
            # 添加到管理器
            self.references[reference.id] = reference
            references.append(reference)
        
        return references
    
    def _calculate_relevance(self, search_result: SearchResult, query: str) -> float:
        """计算搜索结果与查询的相关性"""
        if not query:
            return search_result.score
        
        query_words = set(query.lower().split())
        
        # 标题相关性
        title_words = set(search_result.title.lower().split())
        title_overlap = len(query_words.intersection(title_words)) / len(query_words) if query_words else 0
        
        # 摘要相关性
        snippet_words = set(search_result.snippet.lower().split())
        snippet_overlap = len(query_words.intersection(snippet_words)) / len(query_words) if query_words else 0
        
        # 综合相关性
        relevance = (title_overlap * 0.6 + snippet_overlap * 0.4)
        
        # 结合原始评分
        final_score = (relevance + search_result.score) / 2
        
        return min(1.0, final_score)
    
    def _format_citation(self, reference: Reference, style: str = None) -> str:
        """格式化引用"""
        if style is None:
            style = self.default_style
        
        if style not in self.citation_styles:
            style = self.default_style
        
        citation_style = self.citation_styles[style]
        return citation_style.format_citation(reference)
    
    def get_references(self, 
                      min_credibility: float = 0.0,
                      min_relevance: float = 0.0,
                      limit: Optional[int] = None) -> List[Reference]:
        """获取引用列表"""
        filtered_refs = []
        
        for ref in self.references.values():
            if (ref.credibility_score >= min_credibility and 
                ref.relevance_score >= min_relevance):
                filtered_refs.append(ref)
        
        # 按可信度和相关性排序
        filtered_refs.sort(
            key=lambda x: (x.credibility_score + x.relevance_score) / 2,
            reverse=True
        )
        
        if limit:
            filtered_refs = filtered_refs[:limit]
        
        return filtered_refs
    
    def get_reference_by_id(self, ref_id: str) -> Optional[Reference]:
        """根据ID获取引用"""
        return self.references.get(ref_id)
    
    def remove_duplicates(self) -> int:
        """移除重复引用"""
        seen_urls = set()
        duplicates = []
        
        for ref_id, ref in self.references.items():
            if ref.url in seen_urls:
                duplicates.append(ref_id)
            else:
                seen_urls.add(ref.url)
        
        for ref_id in duplicates:
            del self.references[ref_id]
        
        return len(duplicates)
    
    def generate_bibliography(self, 
                            style: str = 'markdown',
                            min_credibility: float = 0.5) -> str:
        """生成参考文献列表"""
        references = self.get_references(min_credibility=min_credibility)
        
        if not references:
            return "暂无参考文献"
        
        bibliography = ["## 参考文献\n"]
        
        for i, ref in enumerate(references, 1):
            citation = self._format_citation(ref, style)
            bibliography.append(f"{i}. {citation}")
        
        return "\n".join(bibliography)
    
    def get_inline_citations(self, 
                           text: str, 
                           style: str = 'markdown') -> str:
        """在文本中插入内联引用"""
        # 简单的引用插入逻辑
        # 在实际应用中，这里需要更复杂的文本分析
        
        references = self.get_references(min_credibility=0.5, limit=5)
        
        if not references:
            return text
        
        # 在段落末尾添加引用
        paragraphs = text.split('\n\n')
        cited_paragraphs = []
        
        for i, paragraph in enumerate(paragraphs):
            if paragraph.strip():
                # 为每个段落添加相关引用
                relevant_refs = references[:min(2, len(references))]
                citations = []
                
                for ref in relevant_refs:
                    citation = self._format_citation(ref, style)
                    citations.append(citation)
                
                if citations:
                    paragraph += f" ({'; '.join(citations)})"
            
            cited_paragraphs.append(paragraph)
        
        return '\n\n'.join(cited_paragraphs)
    
    def export_references(self, format: str = 'json') -> str:
        """导出引用数据"""
        references_data = [ref.to_dict() for ref in self.references.values()]
        
        if format == 'json':
            import json
            return json.dumps(references_data, indent=2, ensure_ascii=False)
        elif format == 'csv':
            import csv
            import io
            
            output = io.StringIO()
            if references_data:
                writer = csv.DictWriter(output, fieldnames=references_data[0].keys())
                writer.writeheader()
                writer.writerows(references_data)
            
            return output.getvalue()
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取引用统计信息"""
        if not self.references:
            return {
                "total_references": 0,
                "average_credibility": 0.0,
                "average_relevance": 0.0,
                "source_distribution": {},
                "credibility_distribution": {}
            }
        
        total_refs = len(self.references)
        avg_credibility = sum(ref.credibility_score for ref in self.references.values()) / total_refs
        avg_relevance = sum(ref.relevance_score for ref in self.references.values()) / total_refs
        
        # 来源分布
        source_dist = {}
        for ref in self.references.values():
            source_dist[ref.source] = source_dist.get(ref.source, 0) + 1
        
        # 可信度分布
        credibility_ranges = {
            "高 (0.8-1.0)": 0,
            "中 (0.5-0.8)": 0,
            "低 (0.0-0.5)": 0
        }
        
        for ref in self.references.values():
            if ref.credibility_score >= 0.8:
                credibility_ranges["高 (0.8-1.0)"] += 1
            elif ref.credibility_score >= 0.5:
                credibility_ranges["中 (0.5-0.8)"] += 1
            else:
                credibility_ranges["低 (0.0-0.5)"] += 1
        
        return {
            "total_references": total_refs,
            "average_credibility": round(avg_credibility, 3),
            "average_relevance": round(avg_relevance, 3),
            "source_distribution": source_dist,
            "credibility_distribution": credibility_ranges
        }
    
    def clear(self):
        """清空所有引用"""
        self.references.clear()


# 全局引用管理器实例
_reference_manager: Optional[ReferenceManager] = None


def get_reference_manager() -> ReferenceManager:
    """获取全局引用管理器实例"""
    global _reference_manager
    if _reference_manager is None:
        _reference_manager = ReferenceManager()
    return _reference_manager


def reset_reference_manager():
    """重置引用管理器（用于测试）"""
    global _reference_manager
    _reference_manager = None