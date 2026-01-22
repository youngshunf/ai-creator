"""
平台配置加载器

从 YAML 文件或数据库加载平台配置。

@author Ysf
@date 2026-01-22
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from functools import lru_cache

import yaml
from pydantic import ValidationError

try:
    from .schema import PlatformConfig
except ImportError:
    # 支持独立导入测试
    from schema import PlatformConfig

logger = logging.getLogger(__name__)


class ConfigError(Exception):
    """配置错误异常"""
    pass


class ConfigLoader:
    """
    平台配置加载器
    
    支持从以下来源加载配置：
    1. 内置默认配置 (defaults/)
    2. 用户自定义配置目录
    3. 数据库 (未来扩展)
    
    使用示例:
        # 加载单个平台配置
        config = ConfigLoader.load("xiaohongshu")
        
        # 获取所有可用平台
        platforms = ConfigLoader.list_platforms()
        
        # 刷新缓存
        ConfigLoader.refresh_cache()
    """
    
    # 默认配置目录（相对于本文件）
    _defaults_dir: Path = Path(__file__).parent / "defaults"
    
    # 用户自定义配置目录
    _custom_dir: Optional[Path] = None
    
    # 配置缓存
    _cache: Dict[str, PlatformConfig] = {}
    
    # 是否启用缓存
    _cache_enabled: bool = True
    
    @classmethod
    def set_custom_dir(cls, path: str | Path) -> None:
        """
        设置用户自定义配置目录
        
        Args:
            path: 配置目录路径
        """
        cls._custom_dir = Path(path) if isinstance(path, str) else path
        cls.refresh_cache()
    
    @classmethod
    def set_cache_enabled(cls, enabled: bool) -> None:
        """
        设置是否启用缓存
        
        Args:
            enabled: 是否启用
        """
        cls._cache_enabled = enabled
        if not enabled:
            cls._cache.clear()
    
    @classmethod
    def refresh_cache(cls) -> None:
        """清除配置缓存"""
        cls._cache.clear()
    
    @classmethod
    def load(cls, platform_name: str) -> PlatformConfig:
        """
        加载指定平台的配置
        
        优先级：
        1. 缓存
        2. 用户自定义配置目录
        3. 内置默认配置
        
        Args:
            platform_name: 平台名称，如 "xiaohongshu"
            
        Returns:
            PlatformConfig: 平台配置对象
            
        Raises:
            ConfigError: 配置文件不存在或格式错误
        """
        # 检查缓存
        if cls._cache_enabled and platform_name in cls._cache:
            return cls._cache[platform_name]
        
        # 尝试加载配置文件
        config_data = cls._load_yaml(platform_name)
        
        # 验证并创建配置对象
        try:
            config = PlatformConfig(**config_data)
        except ValidationError as e:
            raise ConfigError(
                f"配置验证失败 [{platform_name}]: {e}"
            ) from e
        
        # 缓存
        if cls._cache_enabled:
            cls._cache[platform_name] = config
        
        return config
    
    @classmethod
    def load_all(cls) -> Dict[str, PlatformConfig]:
        """
        加载所有可用平台的配置
        
        Returns:
            Dict[str, PlatformConfig]: 平台名称到配置的映射
        """
        configs = {}
        for platform_name in cls.list_platforms():
            try:
                configs[platform_name] = cls.load(platform_name)
            except ConfigError as e:
                logger.warning(f"加载平台配置失败 [{platform_name}]: {e}")
        return configs
    
    @classmethod
    def list_platforms(cls) -> List[str]:
        """
        列出所有可用的平台名称
        
        Returns:
            List[str]: 平台名称列表
        """
        platforms = set()
        
        # 扫描内置配置目录
        if cls._defaults_dir.exists():
            for f in cls._defaults_dir.glob("*.yaml"):
                platforms.add(f.stem)
            for f in cls._defaults_dir.glob("*.yml"):
                platforms.add(f.stem)
        
        # 扫描自定义配置目录
        if cls._custom_dir and cls._custom_dir.exists():
            for f in cls._custom_dir.glob("*.yaml"):
                platforms.add(f.stem)
            for f in cls._custom_dir.glob("*.yml"):
                platforms.add(f.stem)
        
        return sorted(platforms)
    
    @classmethod
    def _load_yaml(cls, platform_name: str) -> Dict[str, Any]:
        """
        从文件加载 YAML 配置
        
        Args:
            platform_name: 平台名称
            
        Returns:
            Dict: 配置字典
            
        Raises:
            ConfigError: 文件不存在或格式错误
        """
        # 查找配置文件
        config_path = cls._find_config_file(platform_name)
        
        if config_path is None:
            raise ConfigError(f"找不到平台配置文件: {platform_name}")
        
        # 加载 YAML
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigError(f"YAML 解析错误 [{platform_name}]: {e}") from e
        except IOError as e:
            raise ConfigError(f"读取配置文件失败 [{platform_name}]: {e}") from e
        
        if not isinstance(data, dict):
            raise ConfigError(f"配置文件格式错误 [{platform_name}]: 根节点必须是字典")
        
        return data
    
    @classmethod
    def _find_config_file(cls, platform_name: str) -> Optional[Path]:
        """
        查找配置文件路径
        
        优先级：
        1. 用户自定义配置目录
        2. 内置默认配置
        
        Args:
            platform_name: 平台名称
            
        Returns:
            Optional[Path]: 配置文件路径，不存在返回 None
        """
        # 支持的扩展名
        extensions = [".yaml", ".yml"]
        
        # 优先查找自定义配置
        if cls._custom_dir and cls._custom_dir.exists():
            for ext in extensions:
                path = cls._custom_dir / f"{platform_name}{ext}"
                if path.exists():
                    return path
        
        # 查找内置配置
        if cls._defaults_dir.exists():
            for ext in extensions:
                path = cls._defaults_dir / f"{platform_name}{ext}"
                if path.exists():
                    return path
        
        return None
    
    @classmethod
    def validate_config(cls, config_data: Dict[str, Any]) -> List[str]:
        """
        验证配置数据，返回错误列表
        
        Args:
            config_data: 配置字典
            
        Returns:
            List[str]: 错误信息列表，空列表表示验证通过
        """
        errors = []
        
        try:
            PlatformConfig(**config_data)
        except ValidationError as e:
            for error in e.errors():
                loc = ".".join(str(x) for x in error["loc"])
                errors.append(f"{loc}: {error['msg']}")
        
        return errors
    
    @classmethod
    def get_config_path(cls, platform_name: str) -> Optional[Path]:
        """
        获取平台配置文件的路径
        
        Args:
            platform_name: 平台名称
            
        Returns:
            Optional[Path]: 配置文件路径
        """
        return cls._find_config_file(platform_name)
