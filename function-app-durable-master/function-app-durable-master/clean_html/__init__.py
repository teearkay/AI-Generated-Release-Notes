import logging
from bs4 import BeautifulSoup
import azure.functions as func


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    content = req.params.get('content')
    if not content:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            content = req_body.get('content')
    
    if content:
        logging.info(f"Content: {content}")
        cleaned = BeautifulSoup(content, "html.parser").get_text()
        logging.info(f"Cleaned Content: {cleaned}")
        return func.HttpResponse(f"{cleaned}", status_code=200)
    else:
        return func.HttpResponse(
             "Could not parse the content from the request",
             status_code=500
        )