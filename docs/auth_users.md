# Authentication and User Management Documentation

## Authentication

The authentication API provides endpoints for user login, logout, refresh token, forget password, validate code, and reset password.

### Login

*   Endpoint: `POST /api/login`
*   Request body:

    ```json
    {
        "phone_number": "<phone_number>",
        "password": "<password>"
    }
    ```
*   Response:

    ```json
    {
        "tokens": {
            "access": "<access_token>",
            "refresh": "<refresh_token>"
        },
        "user": {
            "uuid": "<user_uuid>",
            "phone_number": "<phone_number>",
            "given_name": "<given_name>",
            "family_name": "<family_name>",
            "email": "<email>",
            "is_staff": <true|false>,
            "is_active": <true|false>,
            "is_verified": <true|false>
        }
    }
    ```

### Logout

*   Endpoint: `GET /api/logout`
*   Headers:

    ```
    Authorization: Bearer <access_token>
    ```
*   Response:

    ```json
    {
        "status": true
    }
    ```

### Refresh Token

*   Endpoint: `POST /api/login/refresh`
*   Request body:

    ```json
    {
        "refresh": "<refresh_token>"
    }
    ```
*   Response:

    ```json
    {
        "access": "<new_access_token>",
        "refresh": "<new_refresh_token>"
    }
    ```

### Forget Password

*   Endpoint: `POST /api/forget-password`
*   Request body:

    ```json
    {
        "phone_number": "<phone_number>"
    }
    ```
*   Response:

    ```json
    {
        "status": true,
        "msg": "OTP generated."
    }
    ```

### Validate Code

*   Endpoint: `POST /api/validate-code`
*   Request body:

    ```json
    {
        "phone_number": "<phone_number>",
        "code": "<verification_code>"
    }
    ```
*   Response:

    ```json
    {
        "status": true,
        "msg": "Code Valid."
    }
    ```

### Reset Password

*   Endpoint: `POST /api/reset-password`
*   Request body:

    ```json
    {
        "phone_number": "<phone_number>",
        "code": "<verification_code>",
        "password": "<new_password>"
    }
    ```
*   Response:

    ```json
    {
        "status": true,
        "msg": "Password Updated."
    }
    ```

## User Management

The user management API provides endpoints for user registration, get user details, update password, verify user, and toggle user activation.

### User Registration

*   Endpoint: `POST /api/register`
*   Request body:

    ```json
    {
        "phone_number": "<phone_number>",
        "password": "<password>",
        "given_name": "<given_name>",
        "family_name": "<family_name>"
    }
    ```
*   Response:

    ```json
    {
        "tokens": {
            "access": "<access_token>",
            "refresh": "<refresh_token>"
        },
        "user_details": {
            "uuid": "<user_uuid>",
            "phone_number": "<phone_number>",
            "given_name": "<given_name>",
            "family_name": "<family_name>",
            "email": "<email>",
            "is_staff": <true|false>,
            "is_active": <true|false>,
            "is_verified": <true|false>
        }
    }
    ```

### Get User Details

*   Endpoint: `GET /api/users/<uuid>`
*   Headers:

    ```
    Authorization: Bearer <access_token>
    ```
*   Response:

    ```json
    {
        "uuid": "<user_uuid>",
        "phone_number": "<phone_number>",
        "given_name": "<given_name>",
        "family_name": "<family_name>",
        "email": "<email>",
        "is_staff": <true|false>,
        "is_active": <true|false>,
        "is_verified": <true|false>
    }
    ```

### Update Password

*   Endpoint: `POST /api/users/<uuid>/update_password`
*   Headers:

    ```
    Authorization: Bearer <access_token>
    ```
*   Request body:

    ```json
    {
        "password": "<new_password>"
    }
    ```
*   Response:

    ```json
    {
        "msg": "Password Updated."
    }
    ```

### Verify User (Staff Only)

*   Endpoint: `GET /api/users/<uuid>/verify`
*   Headers:

    ```
    Authorization: Bearer <access_token>
    ```
*   Response:

    ```json
    {
        "msg": "User Verified."
    }
    ```

### Toggle Activation (Staff Only)

*   Endpoint: `GET /api/users/<uuid>/toggle-activation`
*   Headers:

    ```
    Authorization: Bearer <access_token>
    ```
*   Response:

    ```json
    {
        "msg": "User Verified."
    }