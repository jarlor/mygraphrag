import re
from collections import defaultdict
from typing import Set, Dict

from webserver.configs import settings

pattern = re.compile(r'\[.*?\]')
def get_reference(text: str) -> dict:
    data_dict = defaultdict(set)
    for curr_match in pattern.finditer(text):
        hit_str=curr_match.group()
        key_value_pattern = r'(\w+)\s*\((\d+)\)'
        matches = re.findall(key_value_pattern, hit_str)
        for match in matches:
            key = match[0]
            value = int(match[1])  # 将值转换为整数

            ids = (value,)
            data_dict[key.lower()].update(ids)

    return dict(data_dict)


def generate_ref_links(data: Dict[str, Set[int]], index_id: str) -> list:
    base_url = f"{settings.server_host}:{settings.server_port}/v1/references"
    lines = []
    for key, values in data.items():
        for value in values:
            lines.append(f'[{key.capitalize()}: {value}]({base_url}/{index_id}/{key}/{value})')
    return lines
