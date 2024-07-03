import json
from Bio import Entrez
from datetime import datetime, timedelta, date


def format_date(date_string):
    if date_string is None:
        return None  # or return a default date string
    date_object = datetime.strptime(date_string, '%Y-%m-%d')
    return date_object.strftime('%Y/%m/%d')


class PubmedSearch:

    def __init__(self):
        pass

    @staticmethod
    def get_jcr_value(issn_or_eissn):
        with open('journal_data_2024.json', 'r') as file:
            journal_data = json.load(file)

        # 创建一个查找函数
        for journal in journal_data:
            if journal['ISSN'] == issn_or_eissn or journal['EISSN'] == issn_or_eissn:
                return journal['JIF']
        return " "

    # 定义一个函数来搜索 PubMed
    @staticmethod
    def search_pubmed_ids(keyword, start_date=None, end_date=None, retmax=100):
        # 设置 Entrez 的电子邮件和 API 密钥
        Entrez.email = "sunshinesunbigfly@gmail.com"
        Entrez.api_key = "ded9b0330c52fe2f6020a7a6b8e4b025cf08"

        # If end_date is None, use the current date
        if end_date is None:
            end_date = date.today()
        else:
            end_date = format_date(end_date)

        # If start_date is None, use the date two weeks before end_date
        if start_date is None:
            start_date = end_date - timedelta(weeks=2)
        else:
            start_date = format_date(start_date)

        # 使用 Entrez 的 esearch 方法搜索 PubMed
        handle = Entrez.esearch(db="pubmed", term=keyword, mindate=start_date, maxdate=end_date, retmax=retmax)
        record = Entrez.read(handle)
        handle.close()

        # 获取 PubMed ID 列表
        pubmed_ids = record["IdList"]
        return pubmed_ids

    def get_pubmed_ids_info(self, pubmed_ids_list):
        results = {}
        # 将 PubMed ID 列表转换为逗号分隔的字符串
        pubmed_ids_str = ",".join(pubmed_ids_list)

        # 使用 Entrez 的 efetch 方法获取所有 PubMed ID 的信息
        handle = Entrez.efetch(db="pubmed", id=pubmed_ids_str, rettype="xml", retmode="text")
        records = Entrez.read(handle)
        handle.close()

        # 检查记录列表是否为空
        if not records:
            return results

        # 遍历记录列表中的每个记录
        for record in records['PubmedArticle']:
            # 确保所有子字段都存在，避免进一步的 KeyError
            if "MedlineCitation" in record and "Article" in record["MedlineCitation"]:
                article_data = record["MedlineCitation"]["Article"]
                title = article_data["ArticleTitle"]
                abstract_data = article_data.get("Abstract")
                journal_data = article_data.get("Journal")

                # 从记录中提取 PubMed ID
                pubmed_id = record["MedlineCitation"]["PMID"]

                # 处理可能的 None 值
                abstract = abstract_data["AbstractText"][0] if abstract_data and "AbstractText" in abstract_data and \
                                                               abstract_data[
                                                                   "AbstractText"] else "No abstract available"

                # 提取关键词
                keywords_data = record["MedlineCitation"].get("KeywordList", [])
                keywords = [keyword for keyword_list in keywords_data for keyword in keyword_list]

                # 将关键词添加到摘要中，并用换行符分隔
                abstract_with_keywords = abstract + "<br>Keywords:<br>" + "、".join(keywords)
                abstract = abstract_with_keywords

                journal = journal_data["Title"] if journal_data and "Title" in journal_data else None
                ISSN = journal_data["ISSN"] if journal_data and "ISSN" in journal_data else None
                jour_IF = " "
                if ISSN:
                    jour_IF = self.get_jcr_value(ISSN)

                pub_date = record["MedlineCitation"]["Article"]["Journal"]["JournalIssue"]["PubDate"]
                year = pub_date["Year"] if "Year" in pub_date else None
                month = pub_date["Month"] if "Month" in pub_date else None
                day = pub_date["Day"] if "Day" in pub_date else f"{datetime.today().day:02d}"

                # 如果年、月或日任何一个为None，那么pub_date就为一个空字符串
                if year is None or month is None or day is None:
                    pub_date = ""
                else:
                    pub_date_str = f"{year}-{month}-{day}"
                    try:
                        pub_date = datetime.strptime(pub_date_str, "%Y-%b-%d").date()
                    except ValueError:
                        pub_date = None

                # 将结果添加到结果字典中
                results[str(pubmed_id)] = {
                    'pubmed_id': str(pubmed_id),
                    "title": str(title),
                    "abstract": str(abstract),
                    "journal": str(journal),
                    "publication_date": pub_date,
                    "sciif": jour_IF,
                }
        return results


# 主函数
if __name__ == "__main__":
    pubmed = PubmedSearch()
    pubmed_ids = pubmed.search_pubmed_ids("single cell", retmax=10)
    print(pubmed_ids)
    results = pubmed.get_pubmed_ids_info(pubmed_ids)
    for pmid, result in results.items():
        print("-------------------------------------------")
        print(f"key: {pmid}:")
        print(f"pubmed_id: {result['pubmed_id']}")
        print(f"title: {result['title']}")
        print(f"abstract: {result['abstract']}")
        print(f"journal: {result['journal']}")
        print(f"publication_date: {result['publication_date']}")
        print(f"sciif: {result['sciif']}")
        print("-------------------------------------------\n")
