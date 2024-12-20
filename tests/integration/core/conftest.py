#  Copyright 2024 Red Hat, Inc.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
import pytest

from aap_eda.core import models


@pytest.fixture()
def new_activation(new_user, default_organization):
    return models.Activation.objects.create(
        name="activation",
        user=new_user,
        organization=default_organization,
    )


@pytest.fixture()
def new_rulebook_process_with_activation(new_activation, default_organization):
    return models.RulebookProcess.objects.create(
        name="test-instance",
        activation=new_activation,
        organization=default_organization,
    )
