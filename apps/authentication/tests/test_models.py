from apps.authentication.models import User, UserRole


def test_user_model_exposes_role_choices():
    assert User._meta.get_field("role").choices == UserRole.choices
