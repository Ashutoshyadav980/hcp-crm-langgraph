from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from sqlalchemy.orm import Session
from database.database import get_db
from models import models

SECRET_KEY = os.getenv(
    "JWT_SECRET",
    "supersecretkeyforhealthcarecrmsystemjwttokenauth"
)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode("utf-8")


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return encoded_jwt


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> models.User:

    print("\n========== AUTH DEBUG ==========")

    if credentials is None:
        print("❌ No Authorization header received.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header"
        )

    print("Authorization Scheme:", credentials.scheme)

    token = credentials.credentials
    print("Received Token:", token)

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        print("Decoded JWT Payload:", payload)

        email = payload.get("sub")
        user_id = payload.get("user_id")

        print("Email:", email)
        print("User ID:", user_id)

        if email is None:
            print("❌ Missing 'sub' in JWT")
            raise credentials_exception

        if user_id is None:
            print("❌ Missing 'user_id' in JWT")
            raise credentials_exception

    except JWTError as e:
        print("❌ JWT Decode Error:", str(e))
        raise credentials_exception

    user = (
        db.query(models.User)
        .filter(models.User.id == user_id)
        .first()
    )

    print("Database User:", user)

    if user is None:
        print("❌ User not found in database")
        raise credentials_exception

    print("✅ Authentication Successful")
    print("========== END AUTH DEBUG ==========\n")

    return user