import os
import yaml
from pathlib import Path

def load_yml_and_set_env(service_key: str, config_filename: str = "config.yml"):
    """
    优先加载当前目录下的config.yml，再兜底加载项目根目录下的config.yml，
    只需传递service_key（如base/server/client），自动注入该key下所有配置到os.environ（变量名大写）。
    :param service_key: 服务配置key
    :param config_filename: 配置文件名，默认config.yml
    """
    cwd = Path(__file__).parent.resolve()
    root = cwd.parent.resolve()

    config_paths = [cwd / config_filename, root / config_filename]
    loaded = False
    for config_path in config_paths:
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            print(f"[YML配置] 加载配置文件: {config_path.resolve()}")
            if not isinstance(config, dict):
                raise ValueError(f"YAML配置格式错误: {config_path}")
            service_config = config.get(service_key, {})
            if not isinstance(service_config, dict):
                raise ValueError(f"服务 {service_key} 配置格式错误: {config_path}")
            for k, v in service_config.items():
                os.environ[k.upper()] = str(v)
            loaded = True
            break
    if not loaded:
        raise FileNotFoundError(f"未找到{config_filename}，请在当前目录或根目录下提供配置文件") 