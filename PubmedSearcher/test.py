import json

with open('journal_data_2024.json', 'r') as file:
    journal_data = json.load(file)


# 创建一个查找函数
def find_jif(issn_or_eissn):
    for journal in journal_data:
        if journal['ISSN'] == issn_or_eissn or journal['EISSN'] == issn_or_eissn:
            return journal['JIF']
    return " "


# 示例用法
issn = '0140-6736'
jif = find_jif(issn)
if jif is not None:
    print(f"The JIF for ISSN {issn} is {jif}")
else:
    print(f"No JIF found for ISSN {issn}")
