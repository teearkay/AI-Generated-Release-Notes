# This function an HTTP starter function for Durable Functions.
# Before running this sample, please:
# - create a Durable orchestration function
# - create a Durable activity function (default name is "Hello")
# - add azure-functions-durable to requirements.txt
# - run pip install -r requirements.txt
 
import logging
import json

from azure.functions import HttpRequest, HttpResponse
from azure.durable_functions import DurableOrchestrationClient

def validateinput(inputjson):
    try:
        inputjson = json.loads(inputjson)
        return (True, None)
    except Exception as e:
        logging.error(f"Exception: {str(e)}")
        return (False, str(e))

async def main(req: HttpRequest, starter: str) -> HttpResponse:
    
    client = DurableOrchestrationClient(starter)
    params = req.get_json()
    isSingle = params["single"]
    inputjson = params["payload"]

    isValid, exception = validateinput(inputjson)
    
    if not isValid: 
        return HttpResponse(status_code=400, body=exception)

    inputObj = (isSingle, json.loads(inputjson))
    instance_id = await client.start_new(req.route_params["functionName"], None, inputObj)

    logging.info(f"Started orchestration with ID = '{instance_id}', Input = '{inputObj}'.")

    return client.create_check_status_response(req, instance_id)