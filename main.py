from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
import uuid, os
from pydantic import BaseModel, EmailStr
from typing import Annotated, Union, Optional
import jwt, datetime
from jwt.exceptions import (
    InvalidSignatureError,
    InvalidTokenError,
)
from schemas import *

"""
endpoints
/sign-up-user
/sign-in-user
/delete-user
/update-user
"""

# loading the environment variables
# print("**********************")
# print(secret_key)



database: dict[str, User] = {
    "1": User(
        user_id="1",
        username="metlight",
        hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
        email="hello@bla.com",
    ),
}



class MyCustomException(Exception):
    def __init__(self, status_code: int, error_code: str, detail: str):
        self.status_code = status_code
        self.error_code = error_code
        self.detail = detail


app = FastAPI()


@app.exception_handler(MyCustomException)
async def custom_exception_handler(
    request: Request, exc: MyCustomException
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": exc.error_code,
            "detail": exc.detail,
        },
    )


# authentication functions ---------------------------------------


secret_key = os.environ.get("SECRET")


def create_jwt_token(user: User) -> str:
    # epoch timestamp[1 jan, 1971] / utc timestamp format is used for expiration rate as it compact
    curr_epoch = int(datetime.datetime.now().timestamp())
    payload: dict[str, Union[str, int]] = {
        "iss": "mukal's api",
        "sub": user.user_id,
        "nam": user.username,
        "iat": curr_epoch,
    }

    token: str = jwt.encode(
        payload,
        secret_key,
        algorithm="HS256",
        headers={
            "alg": "HS256",
            "typ": "JWT",
        },
    )
    return token


def validate_jwt_token(received_token: str) -> Union[str, None]:
    try:
        # if the signature matches correctly the token is decoded succesfully
        decoded_token = jwt.decode(received_token, secret_key, algorithms=["HS256"])
        user_id = decoded_token["sub"]

        issue_timestamp = decoded_token["iat"]
        curr_timestamp = int(datetime.datetime.utcnow().timestamp())

        datetime_exp = datetime.datetime.fromtimestamp(issue_timestamp)
        datetime_curr = datetime.datetime.fromtimestamp(curr_timestamp)

        # finding the difference in months
        months_diff = (
            (datetime_curr.year - datetime_exp.year) * 12
            + datetime_curr.month
            - datetime_exp.month
        )

        # checking if the token has not expired
        if months_diff > 6:
            raise MyCustomException(
                status_code=400,
                error_code="token_expired",
                detail="The provided jwt token has expired",
            )

        return user_id

    except InvalidSignatureError:
        raise MyCustomException(
            status_code=400,
            error_code="invalid_signature",
            detail="The provided jwt token has invalid signature",
        )

    except InvalidTokenError:
        raise MyCustomException(
            status_code=400,
            error_code="invalid_token",
            detail="The provided jwt token has invalid signature",
        )


# endpoints ------------------------------------------------


# default endpoint
@app.get("/hello")
def default_endpoint():
    return {
        "Hey": "Welcome to my api",
    }


@app.post("/sign-up/")
async def sign_up_user(json_user: User) -> dict[str, str]:
    """
    Parameter: json_user
    the json_user accepts a dictionary or json object as the path parameter
    """
    jwt_token = None
    try:
        if json_user.user_id == None:
            json_user.user_id = str(uuid.uuid4())[:8]

        for key, value in database.items():
            if key == json_user.user_id:
                raise MyCustomException(
                    status_code=400,
                    error_code="user_id_exists",
                    detail="The particular user or id already exists",
                )

            if value.email == json_user.email:
                raise MyCustomException(
                    status_code=400,
                    error_code="user_already_exists",
                    detail="The user already exists",
                )

        database[id] = json_user
        jwt_token = create_jwt_token(json_user)

    except MyCustomException as custom_exc:
        raise custom_exc

    except:
        raise HTTPException(status_code=500, detail="Internal Server Error")

    return {"jwt_token": jwt_token}


"""
# here we are getting the bearer "parameter" from the header of the request to get the entire header read => https://stackoverflow.com/questions/68231936/how-can-i-get-headers-or-a-specific-header-from-my-backend-api
sign_in_user basically serves the purpose of both an "autologin" and sign in functionality. If the user already has 
valid json token then he can simply pass it in the Bearer parameter of the request header and if its valid he is signed in.
Otherwise a proper username/email + password is required for authentication.
"""


@app.post("/sign-in-user/")
async def sign_in_user(
    user: UserCred, Bearer: Annotated[str | None, Header()] = None
) -> dict:

    try:
        if Bearer:
            user_id = validate_jwt_token(Bearer)
            if user_id:
                return {"user_id": user_id}
        else:
            if (user.user_name == None) and (user.email == None):
                raise MyCustomException(
                    status_code=400,
                    error_code="both_username_&_email_null",
                    detail="Both the username and email can't be None at the same time",
                )

            if user.user_name:
                for key, value in database.items():
                    if (
                        value.username == user.user_name
                        and value.password == user.password
                    ):
                        return {"user_id": key}

            if user.email:
                for key, value in database.items():
                    if value.email == user.email and value.password == user.password:
                        return {"user_id": key}
            raise MyCustomException(
                status_code=404,
                error_code="user_not_found",
                detail="the user with the given credentials do not exist",
            )

    except MyCustomException as custom_exc:
        raise custom_exc

    except:
        raise HTTPException(status_code=500, detail="Internal Server Error")


# @app.put("/del-user/{user_id}")
# async def delete_user(user_id: str) -> dict[str, str]:
#     try:
#         db.reference(f"users/{user_id}").delete()

#         return {"success": "user deleted succesfully"}
#     except:
#         return {"error": "couldn't delete the data"}
