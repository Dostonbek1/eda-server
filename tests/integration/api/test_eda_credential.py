import pytest
from rest_framework import status
from rest_framework.test import APIClient

from aap_eda.core import models
from tests.integration.constants import api_url_v1

INPUTS = {
    "fields": [
        {"id": "username", "label": "Username", "type": "string"},
        {
            "id": "password",
            "label": "Password",
            "type": "string",
            "secret": True,
        },
        {
            "id": "ssh_key_data",
            "label": "SCM Private Key",
            "type": "string",
            "format": "ssh_private_key",
            "secret": True,
            "multiline": True,
        },
        {
            "id": "ssh_key_unlock",
            "label": "Private Key Passphrase",
            "type": "string",
            "secret": True,
        },
    ]
}


@pytest.mark.django_db
def test_create_eda_credential(
    client: APIClient,
    credential_type: models.CredentialType,
):
    data_in = {
        "name": "eda-credential",
        "inputs": {"username": "adam", "password": "secret"},
        "credential_type_id": credential_type.id,
    }
    response = client.post(f"{api_url_v1}/eda-credentials/", data=data_in)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["name"] == "eda-credential"
    assert response.data["managed"] is False


@pytest.mark.django_db
def test_create_eda_credential_with_type(
    client: APIClient, credential_type: models.CredentialType
):
    data_in = {
        "name": "eda-credential",
        "inputs": {"username": "adam", "password": "secret"},
        "credential_type_id": credential_type.id,
    }
    response = client.post(f"{api_url_v1}/eda-credentials/", data=data_in)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["name"] == "eda-credential"
    assert response.data["managed"] is False
    assert response.data["inputs"] == {
        "password": "$encrypted$",
        "username": "adam",
    }


@pytest.mark.django_db
def test_retrieve_eda_credential(
    client: APIClient, credential_type: models.CredentialType
):
    obj = models.EdaCredential.objects.create(
        name="eda_credential",
        inputs={"username": "adam", "password": "secret"},
        managed=False,
        credential_type_id=credential_type.id,
    )
    response = client.get(f"{api_url_v1}/eda-credentials/{obj.id}/")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["name"] == "eda_credential"
    assert response.data["inputs"] == {
        "username": "adam",
        "password": "$encrypted$",
    }
    assert response.data["managed"] is False


@pytest.mark.django_db
def test_list_eda_credentials(
    client: APIClient,
    default_eda_credential: models.EdaCredential,
    default_vault_credential: models.EdaCredential,
    managed_eda_credential: models.EdaCredential,
):
    response = client.get(f"{api_url_v1}/eda-credentials/")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 2
    assert response.data["results"][0]["name"] == default_eda_credential.name
    assert response.data["results"][1]["name"] == default_vault_credential.name


@pytest.mark.django_db
def test_list_eda_credentials_with_kind_filter(
    client: APIClient,
    default_eda_credential: models.EdaCredential,
    default_scm_credential: models.EdaCredential,
):
    response = client.get(
        f"{api_url_v1}/eda-credentials/?credential_type__kind=scm"
    )
    assert len(response.data["results"]) == 1

    response = client.get(
        f"{api_url_v1}/eda-credentials/?credential_type__kind=registry"
    )
    assert len(response.data["results"]) == 1

    response = client.get(
        f"{api_url_v1}/eda-credentials/?credential_type__kind=vault"
    )
    assert len(response.data["results"]) == 0

    response = client.get(
        f"{api_url_v1}/eda-credentials/?credential_type__kind=scm"
        "&credential_type__kind=vault",
    )
    assert len(response.data["results"]) == 1

    response = client.get(
        f"{api_url_v1}/eda-credentials/?credential_type__kind=scm"
        "&credential_type__kind=registry",
    )
    assert len(response.data["results"]) == 2


@pytest.mark.django_db
def test_delete_eda_credential(client: APIClient):
    obj = models.EdaCredential.objects.create(
        name="eda-credential",
        inputs={"username": "adam", "password": "secret"},
    )
    response = client.delete(f"{api_url_v1}/eda-credentials/{obj.id}/")
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert models.EdaCredential.objects.count() == 0


@pytest.mark.django_db
def test_delete_managed_eda_credential(client: APIClient):
    obj = models.EdaCredential.objects.create(
        name="eda-credential",
        inputs={"username": "adam", "password": "secret"},
        managed=True,
    )
    response = client.delete(f"{api_url_v1}/eda-credentials/{obj.id}/")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        response.data["errors"] == "Managed EDA credential cannot be deleted"
    )


@pytest.mark.django_db
def test_partial_update_eda_credential(
    client: APIClient, credential_type: models.CredentialType
):
    obj = models.EdaCredential.objects.create(
        name="eda-credential",
        inputs={"username": "adam", "password": "secret", "key": "private"},
        credential_type_id=credential_type.id,
        managed=True,
    )
    data = {"inputs": {"username": "bearny", "password": "demo"}}
    response = client.patch(
        f"{api_url_v1}/eda-credentials/{obj.id}/", data=data
    )
    assert response.status_code == status.HTTP_200_OK
    result = response.data
    assert result["inputs"] == {
        "password": "$encrypted$",
        "username": "bearny",
        "key": "private",
    }


@pytest.mark.django_db
def test_partial_update_eda_credential_name(
    client: APIClient, credential_type: models.CredentialType
):
    obj = models.EdaCredential.objects.create(
        name="eda-credential",
        inputs={"username": "adam", "password": "secret", "key": "private"},
        credential_type_id=credential_type.id,
        managed=True,
    )
    data = {"name": "demo2"}
    response = client.patch(
        f"{api_url_v1}/eda-credentials/{obj.id}/", data=data
    )
    assert response.status_code == status.HTTP_200_OK
    result = response.data
    assert result["inputs"] == {
        "password": "$encrypted$",
        "username": "adam",
        "key": "private",
    }
    assert result["name"] == "demo2"


@pytest.mark.django_db
def test_delete_credential_used_by_activation(
    default_activation: models.Activation,
    client: APIClient,
    preseed_credential_types,
):
    eda_credential_id = default_activation.eda_credentials.all()[0]
    response = client.delete(
        f"{api_url_v1}/eda-credentials/{eda_credential_id.id}/"
    )
    assert response.status_code == status.HTTP_409_CONFLICT


@pytest.mark.django_db
def test_delete_credential_used_by_activation_forced(
    default_activation: models.Activation,
    client: APIClient,
    preseed_credential_types,
):
    eda_credential = default_activation.eda_credentials.all()[0]
    response = client.delete(
        f"{api_url_v1}/eda-credentials/{eda_credential.id}/?force=true",
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.parametrize("refs", ["true", "false"])
@pytest.mark.django_db
def test_retrieve_eda_credential_with_refs(
    default_activation: models.Activation,
    client: APIClient,
    refs,
    preseed_credential_types,
):
    eda_credential = default_activation.eda_credentials.all()[0]

    response = client.get(
        f"{api_url_v1}/eda-credentials/{eda_credential.id}/?refs={refs}",
    )
    assert response.status_code == status.HTTP_200_OK

    if refs == "true":
        assert response.data["references"] is not None
        references = response.data["references"]

        assert len(references) == 3
        references[0] = {
            "type": "Activation",
            "id": default_activation.id,
            "name": default_activation.name,
            "url": f"api/eda/v1/activations/{default_activation.id}/",
        }
        references[1] = (
            {
                "type": "DecisionEnvironment",
                "id": default_activation.decision_environment.id,
                "name": default_activation.decision_environment.name,
                "url": (
                    "api/eda/v1/decision_environments/"
                    f"{default_activation.decision_environment.id}/"
                ),
            },
        )
        references[1] = {
            "type": "Project",
            "id": default_activation.project.id,
            "name": default_activation.project.name,
            "url": (f"api/eda/v1/projects/{default_activation.project.id}/"),
        }
    else:
        assert response.data["references"] is None
