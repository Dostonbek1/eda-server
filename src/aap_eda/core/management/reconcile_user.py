# flake8: noqa
import logging

from aap_eda.core import models

logger = logging.getLogger("aap_eda.core.management.reconcile_user")


def _add_roles(user, role_name, state):
    role = models.Role.objects.filter(name=role_name).first()
    if role:
        action = "added to"
        if state:
            user.roles.add(role.id)
        else:
            user.roles.remove(role.id)
            action = "removed from"
        logger.info(f"{role_name} role getting {action} {user.username}")
    else:
        raise Exception("No such Role")


class ReconcileUser:
    def reconcile_user_claims(self, user, authenticator_user):
        claims = getattr(user, "claims", getattr(authenticator_user, "claims"))
        logger.error(f"User membership claims: {claims}")

        user_orgs = claims["organization_membership"]
        logger.error(f"User organization membership: {user_orgs}")
        if user_orgs:
            for org, state in user_orgs.items():
                _add_roles(user, org, state)
