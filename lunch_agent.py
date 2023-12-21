from dataclasses import dataclass

from tool_use_package.tools.base_tool import BaseTool
from tool_use_package.tool_user import ToolUser

import requests
from urllib import parse
import os


@dataclass
class BaseRestaurantResult:
    """
    A single search result.
    """

    name: str
    category: str
    source: str


class KakaoMapRestaurantTool(BaseTool):
    def __init__(self,
                 name="search_restaurants_from_kakao_map",
                 description="A tool for finding restaurants through Kakao Maps",
                 parameters=[
                     {"name": "query", "type": "str", "description": "The search term to enter into the Kakao Maps search engine. It shold be a location name or a category name."},
                     {"name": "radius", "type": "int", "description": "The radius of the search area in meters."},
                     {"name": "n_search_results_to_use", "type": "int", "description": "The number of search results to return, where each search result is a restaurant."},
                 ]):
        super().__init__(name, description, parameters)
        self.api_key = os.environ['KAKAO_MAP_API_KEY']

    def use_tool(self, query: str, radius: int, n_search_results_to_use: int):
        print("Query: ", query)

        # Get a location coordinate from the query
        location_result = self.request_keyword_search(query)

        if len(location_result['documents']) == 0:
            return []

        longitude = 0.0
        latitude = 0.0

        for address in location_result['documents']:
            longitude = address['x']
            latitude = address['y']
            break

        search_results = []
        for page in range(1, 100):
            restaurants_result = self.request_category_search(category_group_code='FD6',
                                                              radius=radius,
                                                              longitude=longitude,
                                                              latitude=latitude,
                                                              page=page,
                                                              size=15)

            for restaurant in restaurants_result['documents']:
                if len(search_results) >= n_search_results_to_use:
                    break
                search_results.append(BaseRestaurantResult(name=restaurant['place_name'],
                                                           category=restaurant['category_name'],
                                                           source=restaurant['place_url']))

            if len(search_results) >= n_search_results_to_use:
                break

        print("Restaurants: ", search_results)

        result = KakaoMapRestaurantTool._format_results_full(search_results)
        print(result)

        return result

    @staticmethod
    def _format_results(raw_search_results: list[BaseRestaurantResult]):
        result = "\n".join(
            [
                f'<item index="{i+1}">\n<source>{r.source}</source>\n<restaurant_name>\n{r.name}\n</restaurant_name>\n<category>\n{r.category}\n</category>\n</item>'
                for i, r in enumerate(raw_search_results)
            ]
        )
        return result

    @staticmethod
    def _format_results_full(extracted: list[list[str]]):
        """
        Formats the extracted search results as a string, including the <search_results> tags.

        :param extracted: The extracted search results to format.
        """

        return f"\n<search_results>\n{KakaoMapRestaurantTool._format_results(extracted)}\n</search_results>"

    # 주소만 검색 가능
    def request_address_search(self, query, page=1, size=10):
        address_search_url = "https://dapi.kakao.com/v2/local/search/address.json"
        param = {
            'query': parse.quote(query, encoding='utf-8'),
            'page': page,
            'size': size
        }

        return self.request_api(address_search_url, params=param)

    def request_keyword_search(self, query=None, category_group_code=None, radius=None, longitude=None, latitude=None,
                               page=1, size=10):
        keyword_search_url = "https://dapi.kakao.com/v2/local/search/keyword.json"
        param = {
            'query': query,
            'category_group_code': category_group_code,
            'radius': radius,
            'x': longitude,
            'y': latitude,
            'page': page,
            'size': size
        }
        param = {k: v for k, v in param.items() if v is not None}

        params = parse.urlencode(param)
        return self.request_api(keyword_search_url, params=params)

    def request_category_search(self, category_group_code=None, radius=None, longitude=None, latitude=None,
                                page=1, size=15):
        category_search_url = "https://dapi.kakao.com/v2/local/search/category.json"
        param = {
            'category_group_code': category_group_code,
            'radius': radius,
            'x': longitude,
            'y': latitude,
            'page': page,
            'size': size
        }
        param = {k: v for k, v in param.items() if v is not None}

        params = parse.urlencode(param)
        return self.request_api(category_search_url, params=params)

    def request_api(self, url, params=None):
        headers = {"Authorization": f"KakaoAK {self.api_key}"}
        response = requests.get(url, headers=headers, params=params)
        return response.json()


# Call the tool_user with a prompt to get a version of Claude that can use your tools!
if __name__ == '__main__':
    tool_user = ToolUser([KakaoMapRestaurantTool()])
    messages = [
        {"role": "human", "content": "삼성역 근처에서 매운게 땡길 때 갈만한 식당을 알려줘. 점심 식사야. 최대한 많은 식당 중에서 찾아봐"},
        {"role": "assistant", "content": "너는 훌륭한 식당 추천 에이전트야."
                                         "사람들이 특정 지역 근처를 질문하면 근방 2km 이내의 식당을 추천해줘."}]
    print(tool_user.use_tools(messages=messages, verbose=0.0, execution_mode="automatic"))
å


