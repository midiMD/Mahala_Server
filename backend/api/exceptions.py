from typing import List,LiteralString
from rest_framework.exceptions import ErrorDetail
from rest_framework.views import exception_handler

exceptions_code_map ={
    "email":{"unique":"email_exists"}
}
def convert_exception(key:LiteralString,value:List[ErrorDetail]):

def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)
    print(response.data)
    print(response.exception)
    errors = []
    # Now add the HTTP status code to the response.
    for error in response.data.values:

    if "email" in response.data and response.data["email"][0].code == "unique":
        errors.append(response.data)
        response.data = {"errors":["email_exists",]}
        response.data['status_code'] = response.status_code

    return response