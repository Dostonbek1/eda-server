#  Copyright 2022 Red Hat, Inc.
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

import yaml
from django.db import models

from .base import BaseOrgModel

__all__ = (
    "Rulebook",
    "AuditRule",
)


class Rulebook(BaseOrgModel):
    class Meta:
        db_table = "core_rulebook"
        unique_together = ["project_id", "name"]
        constraints = [
            models.CheckConstraint(
                check=~models.Q(name=""),
                name="ck_rulebook_name_not_empty",
            ),
        ]
        default_permissions = ("view",)

    name = models.TextField(null=False)
    description = models.TextField(null=True, default="")
    # TODO: this field should not have a default value.
    # TODO: should the content of this field be validated?
    # https://issues.redhat.com/browse/AAP-19202
    rulesets = models.TextField(null=False, default="")
    project = models.ForeignKey("Project", on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=False)
    modified_at = models.DateTimeField(auto_now=True, null=False)

    # For instrospection purposes we need to return
    # rulesets data unserialized.
    def get_rulesets_data(self) -> list[dict]:
        """Return rulesets data as a list of dicts."""
        try:
            return yaml.safe_load(self.rulesets)
        except yaml.YAMLError as e:
            raise ValueError(
                (
                    "Unable to parse rulesets data for rulebook "
                    f" {self.id} - {self.name}: Error: {e}"
                )
            )


class AuditRule(BaseOrgModel):
    router_basename = "auditrule"

    class Meta:
        db_table = "core_audit_rule"
        indexes = [
            models.Index(fields=["name"], name="ix_audit_rule_name"),
            models.Index(fields=["fired_at"], name="ix_audit_rule_fired_at"),
        ]
        ordering = ("-fired_at",)
        default_permissions = ("view",)

    name = models.TextField(null=False)
    status = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True, null=False)
    fired_at = models.DateTimeField(null=False)
    rule_uuid = models.UUIDField(null=True)
    ruleset_uuid = models.UUIDField(null=True)
    ruleset_name = models.TextField(null=True)
    activation_instance = models.ForeignKey(
        "RulebookProcess", on_delete=models.SET_NULL, null=True
    )
    job_instance = models.ForeignKey(
        "JobInstance", on_delete=models.SET_NULL, null=True
    )


class AuditAction(models.Model):
    class Meta:
        db_table = "core_audit_action"
        unique_together = ["id", "name"]
        ordering = ("-fired_at", "-rule_fired_at")

    id = models.UUIDField(primary_key=True)
    name = models.TextField()
    status = models.TextField(blank=True)
    url = models.URLField(blank=True)
    fired_at = models.DateTimeField()
    rule_fired_at = models.DateTimeField(null=True)
    status_message = models.TextField(null=True, default=None)

    audit_rule = models.ForeignKey(
        "AuditRule", on_delete=models.CASCADE, null=True
    )


class AuditEvent(models.Model):
    class Meta:
        db_table = "core_audit_event"
        ordering = ("-received_at", "-rule_fired_at")

    id = models.UUIDField(primary_key=True)
    source_name = models.TextField()
    source_type = models.TextField()
    received_at = models.DateTimeField()
    payload = models.JSONField(null=True)
    rule_fired_at = models.DateTimeField(null=True)

    audit_actions = models.ManyToManyField(
        "AuditAction", related_name="audit_events"
    )
