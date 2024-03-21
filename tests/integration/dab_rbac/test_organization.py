import pytest
from django.apps import apps
from django.core.exceptions import FieldDoesNotExist
from django.urls.exceptions import NoReverseMatch
from rest_framework.reverse import reverse

from tests.integration.dab_rbac.conftest import ModelFactory


def has_field(cls, field_name):
    try:
        cls._meta.get_field(field_name)
        return True
    except FieldDoesNotExist:
        return False


ORG_MODELS = [
    cls
    for cls in apps.all_models["core"].values()
    if has_field(cls, "organization")
]


@pytest.fixture
def cls_factory(admin_user):  # noqa: F811
    "We want this to be for admin user for this module"
    return ModelFactory(admin_user)


@pytest.mark.django_db
@pytest.mark.parametrize("model", ORG_MODELS)
def test_create_with_default_org(cls_factory, model, admin_api_client):
    create_data = cls_factory.get_create_data(model)
    data = cls_factory.get_post_data(model, create_data)
    assert "organization_id" in data  # sanity
    data.pop("organization_id")

    if model._meta.model_name == "team":
        pytest.skip("Team model requires an organization")

    try:
        url = reverse(f"{model._meta.model_name}-list")
    except NoReverseMatch:
        pytest.skip("Not testing model for now")

    response = admin_api_client.post(url, data=data, format="json")

    if response.status_code == 405:
        pytest.skip("Not testing model not allowing creation for now")

    assert response.status_code == 201, response.data
    # organization_id is inconsistentently given in response so not using that

    if model.objects.count() == 1:
        obj = model.objects.first()
    elif "name" in response.data:
        obj = model.objects.get(name=response.data["name"])
    else:
        obj = model.objects.get(pk=response.data["id"])

    assert obj.organization_id
    assert obj.organization.name == "Default"


@pytest.mark.django_db
@pytest.mark.parametrize("model", ORG_MODELS)
def test_create_with_custom_org(cls_factory, model, admin_api_client):
    create_data = cls_factory.get_create_data(model)
    data = cls_factory.get_post_data(model, create_data)
    assert "organization_id" in data  # sanity
    assert create_data["organization"].name != "Default"

    try:
        url = reverse(f"{model._meta.model_name}-list")
    except NoReverseMatch:
        pytest.skip("Not testing model with no list view for now")

    response = admin_api_client.post(url, data=data, format="json")

    if response.status_code == 405:
        pytest.skip("Not testing model not allowing creation for now")

    assert response.status_code == 201, response.data

    if model.objects.count() == 1:
        obj = model.objects.first()
    elif "name" in response.data:
        obj = model.objects.get(name=response.data["name"])
    else:
        obj = model.objects.get(pk=response.data["id"])

    assert obj.organization_id == data["organization_id"]