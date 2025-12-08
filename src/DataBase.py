from typing import Dict, List, Optional
from pymongo import MongoClient
from pymongo.collection import Collection
from langchain.tools import tool

class TemplateDB:
    def __init__(
        self,
        uri: str = "mongodb://localhost:27017/",
        db_name: str = "templates_db",
        collection_name: str = "templates",
    ):
        self.client: MongoClient = MongoClient(uri)
        self.db = self.client[db_name]
        self.collection: Collection = self.db[collection_name]
    def add_template(

        self,
        name: str,
        fields_csv: str,
        md_text: str,
    ) -> Dict:
        """
        Добавляет шаблон.
        :param name: название шаблона (строка)
        :param fields_csv: заполняемые поля, строка с разделителем, например: "field1,field2,field3"
        :param md_text: текст файла в формате Markdown (строка), с указанием, где находятся fields1, fields2
        :return: сохранённый шаблон как словарь
        """
        fields: List[str] = [f.strip() for f in fields_csv.split(",") if f.strip()]

        doc: Dict = {
            "name": name,
            "fields": fields,
            "text_md": md_text,
        }

        # upsert по названию: либо создаём, либо обновляем существующий
        self.collection.update_one(
            {"name": name},
            {"$set": doc},
            upsert=True,
        )

        # возвращаем актуальный документ
        saved: Optional[Dict] = self.collection.find_one({"name": name})
        return saved if saved is not None else doc
    def get_template(self,name: str) -> dict | None:
        """
        Получить шаблон по названию.
        :param name: название шаблона
        :return: словарь с шаблоном или None, если не найден
        """
        return self.collection.find_one({"name": name})

    def get_all_templates(self) -> list[dict]:
        """
        Получить все шаблоны из базы в виде списка словарей.
        :return: список шаблонов
        """
        return list(self.collection.find({}))
