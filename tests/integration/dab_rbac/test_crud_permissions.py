import pytest
from ansible_base.rbac import permission_registry
from ansible_base.rbac.models import RoleDefinition
from django.contrib.contenttypes.models import ContentType
from django.urls.exceptions import NoReverseMatch
from rest_framework.reverse import reverse

from aap_eda.core.models import DABPermission


@pytest.mark.django_db
@pytest.mark.parametrize("model", permission_registry.all_registered_models)
def test_factory_sanity(model, cls_factory):
    cls_factory.create(model)


@pytest.mark.django_db
@pytest.mark.parametrize("model", permission_registry.all_registered_models)
def test_add_permissions(
    model, cls_factory, user, user_api_client, give_obj_perm
):
    create_data = cls_factory.get_create_data(model)
    data = cls_factory.get_post_data(model, create_data)
    if "add" not in model._meta.default_permissions:
        pytest.skip("Model has no add permission")

    url = reverse(f"{model._meta.model_name}-list")

    response = user_api_client.post(url, data=data)
    assert response.status_code == 403, response.data

    # Figure out the parent object if we can
    parent_field_name = permission_registry.get_parent_fd_name(model)
    if parent_field_name:
        parent_obj = create_data[parent_field_name]
        add_rd = RoleDefinition.objects.create(
            name=f"add-{model._meta.model_name}",
            content_type=ContentType.objects.get_for_model(parent_obj),
        )
        add_rd.permissions.add(
            DABPermission.objects.get(codename=f"add_{model._meta.model_name}")
        )
        add_rd.give_permission(user, parent_obj)
        assert user.has_obj_perm(
            parent_obj, f"add_{model._meta.model_name}"
        )  # sanity
    else:
        # otherwise give global add permission for this model
        add_rd = RoleDefinition.objects.create(
            name=f"add-{model._meta.model_name}-global", content_type=None
        )
        add_rd.give_global_permission(user)

    response = user_api_client.post(url, data=data, format="json")
    assert response.status_code == 201, response.data


def get_detail_url(obj, skip_if_not_found=False):
    try:
        return reverse(f"{obj._meta.model_name}-detail", kwargs={"pk": obj.pk})
    except NoReverseMatch:
        if skip_if_not_found:
            pytest.skip("Missing view is reported in test_view_permissions")
        raise


@pytest.mark.django_db
@pytest.mark.parametrize("model", permission_registry.all_registered_models)
def test_view_permissions(
    model, cls_factory, user, user_api_client, give_obj_perm
):
    obj = cls_factory.create(model)
    # We are not skipping any models, all models should have view permission

    url = get_detail_url(obj)

    # Subtle - server should not indicate whether object exists or not, 404
    response = user_api_client.get(url, data={})
    assert response.status_code == 404, response.data

    # with view permission, a GET should be successful
    give_obj_perm(user, obj, "view")
    response = user_api_client.get(url, data={})
    assert response.status_code == 200, response.data


@pytest.mark.django_db
@pytest.mark.parametrize("model", permission_registry.all_registered_models)
def test_change_permissions(
    model, cls_factory, user, user_api_client, give_obj_perm
):
    obj = cls_factory.create(model)
    if "change" not in obj._meta.default_permissions:
        pytest.skip("Model has no change permission")

    url = get_detail_url(obj, skip_if_not_found=True)

    # Attempted PATCH without permission should give a 403
    give_obj_perm(user, obj, "view")
    response = user_api_client.patch(url, data={})
    assert response.status_code == 403, response.data

    # Give object change permission
    give_obj_perm(user, obj, "change")
    response = user_api_client.patch(url, data={})
    assert response.status_code == 200, response.data


@pytest.mark.django_db
@pytest.mark.parametrize("model", permission_registry.all_registered_models)
def test_delete_permissions(
    model, cls_factory, user, user_api_client, give_obj_perm
):
    obj = cls_factory.create(model)
    if "delete" not in obj._meta.default_permissions:
        pytest.skip("Model has no delete permission")

    url = get_detail_url(obj, skip_if_not_found=True)

    # Attempted DELETE without permission should give a 403
    give_obj_perm(user, obj, "view")
    response = user_api_client.delete(url)
    assert response.status_code == 403, response.data

    # Create and give object role
    give_obj_perm(user, obj, "delete")
    response = user_api_client.delete(url)
    assert response.status_code == 204, response.data