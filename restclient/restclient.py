import json
import uuid

import allure
import curlify
import requests.exceptions
import structlog
from requests import session, Response


def allure_attach(fn):
    def wrapper(*args, **kwargs):
        body = kwargs.get('json')
        if body:
            allure.attach(
                json.dumps(kwargs.get('json'), indent=2),
                name='request',
                attachment_type=allure.attachment_type.JSON
            )

        response = fn(*args, **kwargs)
        try:
            response_json = response.json()
        except requests.exceptions.JSONDecodeError:
            response_text = response.text
            status_code = f'<status_code {response.status_code}>'
            allure.attach(
                response_text if len(response_text) > 0 else status_code,
                name='response',
                attachment_type=allure.attachment_type.TEXT
            )
        else:
            allure.attach(
                json.dumps(response_json, indent=2),
                name='response',
                attachment_type=allure.attachment_type.JSON
            )
        return response

    return wrapper


class Restclient:
    def __init__(self, host, headers=None):
        self.host = host
        self.headers = headers
        self.session = session()
        if headers:
            self.session.headers.update(headers)
        self.log = structlog.getLogger(self.__class__.__name__).bind(service="api")
        # (в скобках после getLogger мы передали название класса Restclient. bing - подсказывает нам, что это лог)

        # пишем обертки для каждого из методов, которые возвращают какой либо обернутый запрос

    @allure_attach
    def post(self, path: str, **kwargs) -> Response:
        return self._send_request("POST", path, **kwargs)

    @allure_attach
    def get(self, path: str, **kwargs) -> Response:
        return self._send_request("GET", path, **kwargs)

    @allure_attach
    def put(self, path: str, **kwargs) -> Response:
        return self._send_request("PUT", path, **kwargs)

    @allure_attach
    def delete(self, path: str, **kwargs) -> Response:
        return self._send_request("DELETE", path, **kwargs)

        # пишем метод send_request, который принимает запрос, оборачивает его в лог и отдает обернутый запрос.
        # принимаемые аргументы: method (post,get,put...), path (эндпоинт), kwargs)

    def _send_request(self, method, path, **kwargs):
        full_url = self.host + path
        log = self.log.bind(event_id=str(
            uuid.uuid4()))  # инициализируем лог и присваиваем ему ключ с ID события, кот-й сразу преобразуем в строку, так как uuid отдает байтовую строку
        # формируем сам лог,где прописываем данные, кот-е хотим видеть)
        log.msg(
            event="request",
            method=method,
            full_url=full_url,
            params=kwargs.get("params"),  # читаем из переменных аргументов при помощи метода get
            headers=kwargs.get("headers"),
            json=kwargs.get('json'),  # если это запрос, то мы увидим json, который отправляем
            data=kwargs.get('data')  # если в запросе данные передаются не json а в формате строки
        )
        # передаем результат нашего запроса (метода send_request)
        response = self.session.request(
            method=method,
            url=full_url,
            **kwargs
        )

        # создаем CURL, чтобы наш запрос можно было юзать в постмане или слать разрабу

        curl = curlify.to_curl(response.request)
        allure.attach(
            curl,
            name='CURL',
            attachment_type=allure.attachment_type.TEXT
        )
        # объект request у нас хранится в переменной response) Здесь мы и получим сurl
        print(curl)

        # создаем ответ от сервера, который мы получим после нашего запроса

        log.msg(
            event="response",
            status_code=response.status_code,
            headers=response.headers,
            json=self._get_json(response),
            text=response.text,
            content=response.content,
            curl=curl
        )
        return response

        # создадим функцию, которая будет поверять: возвращается ли нам json и в случае, если нет - то вместо огромной ошибки вернет нам пустое значение

    @staticmethod
    def _get_json(response):
        try:
            return response.json()
        except requests.exceptions.JSONDecodeError:
            return
