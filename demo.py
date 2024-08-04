import re
from collections import defaultdict

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
            data_dict[key].update(ids)

    return dict(data_dict)



if __name__ == '__main__':
    context="""### 国内市场

国内市场的竞争激烈，利润空间较小。以“新天”为例，其国内设备几乎不挣钱，主要依靠海外市场获取更高利润 [Data: Entities (11)]. “国宏”主要销售国内市场，虽然对外销售量不大，但预计在2024年会加大国外订单的比例 [Data: Entities (12)]. 此外，“森峰”在国内市场面临售后人员大规模离职的问题，预计今年会扩招20人左右 [Data: Entities (33)].

国内市场的客户对产品的稳定性和易用性要求越来越高 [Data: Entities (27)]. 例如，“产品B”的用户反馈其稳定性有待提高，频繁崩 溃 [Data: Entities (148)]. 另外，国内市场的竞争对手也在不断推出新功能吸引用户，如“竞争对手C” [Data: Entities (149)].

### 海外市场

相比之下，海外市场的利润更高，且客户需求有所不同。例如，“新天”的海外设备利润比国内高20%，且海外客户更在意机床占地面积和 单位面积产能 [Data: Entities (11)]. “唯拓”主要做海外订单，并且承认S9驱动器性能优于汇川，但对账期有要求 [Data: Entities (105); Relationships (38)].

印度市场是一个价格敏感且环境较差的市场，当地已有部分OEM厂家，价格上有优势 [Data: Entities (36)]. “中亚”市场对高功率激光 设备有需求，并且对BLT和系统有价格诉求 [Data: Entities (81)]. “梅萨尔”在高功率平面市场中表现突出，对S9驱动器的年度价格协 议感到满意，显示出其在行业内的竞争力 [Data: Entities (100); Relationships (36)].

### 市场动向与策略

在市场策略方面，“德马克”主推2000E总线系统，主要客户为海外大客户 [Data: Entities (109); Relationships (42)]. “新天”的售后主管李善威反馈，除非客户指定维宏系统，一般都是柏楚系统，维宏系统一年能有用5套左右 [Data: Entities (30, 18); Relationships (9)].

此外，市场调研显示，客户对软件的稳定性和易用性要求越来越高，这对企业的产品开发和市场推广提出了更高的要求 [Data: Entities (27)]. 例如，“BUG53814”反映了hypcut生产报告单切割总长与其他产品差距较大的问题，这些技术问题需要及时解决以满足客户需求 [Data: Sources (0)].

### 结论

总体来看，国内市场竞争激烈，利润空间有限，而海外市场则提供了更高的利润和不同的客户需求。企业需要根据不同市场的特点制定相应的策略，以提高市场份额和客户满意度。通过不断优化产品性能和售后服务，企业可以在激烈的市场竞争中保持优势。"""

    print(get_reference(context))