import pytest

from .depends import requires_admin_user, requires_user, verify_user


def test_verify_user_no_payload():
    # Payload olmadan kullanıcı doğrulama testi
    user = verify_user(None, admin_only=False)
    assert user.user_id == "3e53486c-cf57-477e-ba2a-cb02dc828e1a"
    assert user.role == "admin"


def test_verify_user_no_user_id():
    # Kullanıcı ID'si olmadan kullanıcı doğrulama testi
    with pytest.raises(Exception):
        verify_user({"role": "admin"}, admin_only=False)


def test_verify_user_not_admin():
    # Admin olmayan kullanıcı doğrulama testi
    with pytest.raises(Exception):
        verify_user(
            {"sub": "3e53486c-cf57-477e-ba2a-cb02dc828e1a", "role": "user"},
            admin_only=True,
        )


def test_verify_user_with_admin_role():
    # Admin rolü ile kullanıcı doğrulama testi
    user = verify_user(
        {"sub": "3e53486c-cf57-477e-ba2a-cb02dc828e1a", "role": "admin"},
        admin_only=True,
    )
    assert user.user_id == "3e53486c-cf57-477e-ba2a-cb02dc828e1a"
    assert user.role == "admin"


def test_verify_user_with_user_role():
    # Kullanıcı rolü ile kullanıcı doğrulama testi
    user = verify_user(
        {"sub": "3e53486c-cf57-477e-ba2a-cb02dc828e1a", "role": "user"},
        admin_only=False,
    )
    assert user.user_id == "3e53486c-cf57-477e-ba2a-cb02dc828e1a"
    assert user.role == "user"


def test_requires_user():
    # Kullanıcı gereksinimi testi
    user = requires_user(
        {"sub": "3e53486c-cf57-477e-ba2a-cb02dc828e1a", "role": "user"}
    )
    assert user.user_id == "3e53486c-cf57-477e-ba2a-cb02dc828e1a"
    assert user.role == "user"


def test_requires_user_no_user_id():
    # Kullanıcı ID'si olmadan kullanıcı gereksinimi testi
    with pytest.raises(Exception):
        requires_user({"role": "user"})


def test_requires_admin_user():
    # Admin kullanıcı gereksinimi testi
    user = requires_admin_user(
        {"sub": "3e53486c-cf57-477e-ba2a-cb02dc828e1a", "role": "admin"}
    )
    assert user.user_id == "3e53486c-cf57-477e-ba2a-cb02dc828e1a"
    assert user.role == "admin"


def test_requires_admin_user_not_admin():
    # Admin olmayan kullanıcı gereksinimi testi
    with pytest.raises(Exception):
        requires_admin_user(
            {"sub": "3e53486c-cf57-477e-ba2a-cb02dc828e1a", "role": "user"}
        )
