from __future__ import annotations

from typing import Any

from hivehook.types import Organization, OTLPConfig, ListResult
from hivehook.resources._base import parse_page_info, build_list_vars

_ORG_FIELDS = """
    id name slug ssoEnabled ssoProvider
    retentionEvents retentionMessages
    otlpConfig { endpoint headers insecure sampleRate }
    createdAt updatedAt
"""

_LIST_QUERY = """
query ListOrganizations($search: String, $limit: Int, $offset: Int) {
  organizations(search: $search, limit: $limit, offset: $offset) {
    nodes { %s }
    pageInfo { total limit offset endCursor hasNextPage }
  }
}
""" % _ORG_FIELDS

_GET_QUERY = """
query GetOrganization($id: UUID!) {
  organization(id: $id) { %s }
}
""" % _ORG_FIELDS

_CREATE_MUTATION = """
mutation CreateOrganization($input: CreateOrganizationInput!) {
  createOrganization(input: $input) { %s }
}
""" % _ORG_FIELDS

_UPDATE_MUTATION = """
mutation UpdateOrganization($id: UUID!, $input: UpdateOrganizationInput!) {
  updateOrganization(id: $id, input: $input) { %s }
}
""" % _ORG_FIELDS

_DELETE_MUTATION = """
mutation DeleteOrganization($id: UUID!) {
  deleteOrganization(id: $id)
}
"""

_CONFIGURE_SSO_MUTATION = """
mutation ConfigureSSO($organizationId: UUID!, $input: SSOConfigInput!) {
  configureSSO(organizationId: $organizationId, input: $input) { %s }
}
""" % _ORG_FIELDS

_DISABLE_SSO_MUTATION = """
mutation DisableSSO($organizationId: UUID!) {
  disableSSO(organizationId: $organizationId) { %s }
}
""" % _ORG_FIELDS

_UPDATE_RETENTION_MUTATION = """
mutation UpdateOrganizationRetention($organizationId: UUID!, $input: RetentionInput!) {
  updateOrganizationRetention(organizationId: $organizationId, input: $input) { %s }
}
""" % _ORG_FIELDS

_DELETE_DATA_MUTATION = """
mutation DeleteOrganizationData($organizationId: UUID!) {
  deleteOrganizationData(organizationId: $organizationId)
}
"""

_EXPORT_DATA_MUTATION = """
mutation ExportOrganizationData($organizationId: UUID!) {
  exportOrganizationData(organizationId: $organizationId)
}
"""

_CONFIGURE_OTLP_MUTATION = """
mutation ConfigureOTLP($organizationId: UUID!, $input: OTLPConfigInput!) {
  configureOTLP(organizationId: $organizationId, input: $input) { %s }
}
""" % _ORG_FIELDS

_DISABLE_OTLP_MUTATION = """
mutation DisableOTLP($organizationId: UUID!) {
  disableOTLP(organizationId: $organizationId) { %s }
}
""" % _ORG_FIELDS


def _parse_otlp_config(data: dict[str, Any] | None) -> OTLPConfig | None:
    if data is None:
        return None
    return OTLPConfig(
        endpoint=data.get("endpoint", ""),
        headers=data.get("headers"),
        insecure=data.get("insecure", False),
        sample_rate=data.get("sampleRate", 0.0),
    )


def _parse_organization(data: dict[str, Any]) -> Organization:
    return Organization(
        id=data.get("id", ""),
        name=data.get("name", ""),
        slug=data.get("slug", ""),
        sso_enabled=data.get("ssoEnabled", False),
        sso_provider=data.get("ssoProvider"),
        retention_events=data.get("retentionEvents", 0),
        retention_messages=data.get("retentionMessages", 0),
        otlp_config=_parse_otlp_config(data.get("otlpConfig")),
        created_at=data.get("createdAt", ""),
        updated_at=data.get("updatedAt", ""),
    )


class OrganizationService:
    def __init__(self, transport: Any):
        self._t = transport

    def list(
        self, search: str | None = None,
        limit: int | None = None, offset: int | None = None,
    ) -> ListResult[Organization]:
        v = build_list_vars(limit=limit, offset=offset, search=search)
        data = self._t.execute(_LIST_QUERY, v)
        conn = data["organizations"]
        return ListResult(
            nodes=[_parse_organization(n) for n in conn["nodes"]],
            page_info=parse_page_info(conn),
        )

    def get(self, id: str) -> Organization | None:
        data = self._t.execute(_GET_QUERY, {"id": id})
        o = data.get("organization")
        return _parse_organization(o) if o else None

    def create(self, name: str, slug: str) -> Organization:
        inp: dict[str, Any] = {"name": name, "slug": slug}
        data = self._t.execute(_CREATE_MUTATION, {"input": inp})
        return _parse_organization(data["createOrganization"])

    def update(self, id: str, **kwargs: Any) -> Organization:
        inp: dict[str, Any] = {}
        if "name" in kwargs:
            inp["name"] = kwargs["name"]
        if "slug" in kwargs:
            inp["slug"] = kwargs["slug"]
        data = self._t.execute(_UPDATE_MUTATION, {"id": id, "input": inp})
        return _parse_organization(data["updateOrganization"])

    def delete(self, id: str) -> bool:
        data = self._t.execute(_DELETE_MUTATION, {"id": id})
        return data.get("deleteOrganization", False)

    def configure_sso(
        self, organization_id: str, provider: str,
        idp_metadata_url: str | None = None,
        entity_id: str | None = None,
        acs_base_url: str | None = None,
        issuer: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        redirect_url: str | None = None,
    ) -> Organization:
        inp: dict[str, Any] = {"provider": provider}
        if idp_metadata_url is not None:
            inp["idpMetadataUrl"] = idp_metadata_url
        if entity_id is not None:
            inp["entityId"] = entity_id
        if acs_base_url is not None:
            inp["acsBaseUrl"] = acs_base_url
        if issuer is not None:
            inp["issuer"] = issuer
        if client_id is not None:
            inp["clientId"] = client_id
        if client_secret is not None:
            inp["clientSecret"] = client_secret
        if redirect_url is not None:
            inp["redirectUrl"] = redirect_url
        data = self._t.execute(_CONFIGURE_SSO_MUTATION, {"organizationId": organization_id, "input": inp})
        return _parse_organization(data["configureSSO"])

    def disable_sso(self, organization_id: str) -> Organization:
        data = self._t.execute(_DISABLE_SSO_MUTATION, {"organizationId": organization_id})
        return _parse_organization(data["disableSSO"])

    def update_retention(
        self, organization_id: str, retention_events: int, retention_messages: int,
    ) -> Organization:
        inp: dict[str, Any] = {"retentionEvents": retention_events, "retentionMessages": retention_messages}
        data = self._t.execute(_UPDATE_RETENTION_MUTATION, {"organizationId": organization_id, "input": inp})
        return _parse_organization(data["updateOrganizationRetention"])

    def delete_data(self, organization_id: str) -> bool:
        data = self._t.execute(_DELETE_DATA_MUTATION, {"organizationId": organization_id})
        return data.get("deleteOrganizationData", False)

    def export_data(self, organization_id: str) -> Any:
        data = self._t.execute(_EXPORT_DATA_MUTATION, {"organizationId": organization_id})
        return data.get("exportOrganizationData")

    def configure_otlp(
        self, organization_id: str, endpoint: str,
        headers: dict[str, str] | None = None,
        insecure: bool | None = None,
        sample_rate: float | None = None,
    ) -> Organization:
        inp: dict[str, Any] = {"endpoint": endpoint}
        if headers is not None:
            inp["headers"] = headers
        if insecure is not None:
            inp["insecure"] = insecure
        if sample_rate is not None:
            inp["sampleRate"] = sample_rate
        data = self._t.execute(_CONFIGURE_OTLP_MUTATION, {"organizationId": organization_id, "input": inp})
        return _parse_organization(data["configureOTLP"])

    def disable_otlp(self, organization_id: str) -> Organization:
        data = self._t.execute(_DISABLE_OTLP_MUTATION, {"organizationId": organization_id})
        return _parse_organization(data["disableOTLP"])


class AsyncOrganizationService:
    def __init__(self, transport: Any):
        self._t = transport

    async def list(
        self, search: str | None = None,
        limit: int | None = None, offset: int | None = None,
    ) -> ListResult[Organization]:
        v = build_list_vars(limit=limit, offset=offset, search=search)
        data = await self._t.execute(_LIST_QUERY, v)
        conn = data["organizations"]
        return ListResult(
            nodes=[_parse_organization(n) for n in conn["nodes"]],
            page_info=parse_page_info(conn),
        )

    async def get(self, id: str) -> Organization | None:
        data = await self._t.execute(_GET_QUERY, {"id": id})
        o = data.get("organization")
        return _parse_organization(o) if o else None

    async def create(self, name: str, slug: str) -> Organization:
        inp: dict[str, Any] = {"name": name, "slug": slug}
        data = await self._t.execute(_CREATE_MUTATION, {"input": inp})
        return _parse_organization(data["createOrganization"])

    async def update(self, id: str, **kwargs: Any) -> Organization:
        inp: dict[str, Any] = {}
        if "name" in kwargs:
            inp["name"] = kwargs["name"]
        if "slug" in kwargs:
            inp["slug"] = kwargs["slug"]
        data = await self._t.execute(_UPDATE_MUTATION, {"id": id, "input": inp})
        return _parse_organization(data["updateOrganization"])

    async def delete(self, id: str) -> bool:
        data = await self._t.execute(_DELETE_MUTATION, {"id": id})
        return data.get("deleteOrganization", False)

    async def configure_sso(
        self, organization_id: str, provider: str,
        idp_metadata_url: str | None = None,
        entity_id: str | None = None,
        acs_base_url: str | None = None,
        issuer: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        redirect_url: str | None = None,
    ) -> Organization:
        inp: dict[str, Any] = {"provider": provider}
        if idp_metadata_url is not None:
            inp["idpMetadataUrl"] = idp_metadata_url
        if entity_id is not None:
            inp["entityId"] = entity_id
        if acs_base_url is not None:
            inp["acsBaseUrl"] = acs_base_url
        if issuer is not None:
            inp["issuer"] = issuer
        if client_id is not None:
            inp["clientId"] = client_id
        if client_secret is not None:
            inp["clientSecret"] = client_secret
        if redirect_url is not None:
            inp["redirectUrl"] = redirect_url
        data = await self._t.execute(_CONFIGURE_SSO_MUTATION, {"organizationId": organization_id, "input": inp})
        return _parse_organization(data["configureSSO"])

    async def disable_sso(self, organization_id: str) -> Organization:
        data = await self._t.execute(_DISABLE_SSO_MUTATION, {"organizationId": organization_id})
        return _parse_organization(data["disableSSO"])

    async def update_retention(
        self, organization_id: str, retention_events: int, retention_messages: int,
    ) -> Organization:
        inp: dict[str, Any] = {"retentionEvents": retention_events, "retentionMessages": retention_messages}
        data = await self._t.execute(_UPDATE_RETENTION_MUTATION, {"organizationId": organization_id, "input": inp})
        return _parse_organization(data["updateOrganizationRetention"])

    async def delete_data(self, organization_id: str) -> bool:
        data = await self._t.execute(_DELETE_DATA_MUTATION, {"organizationId": organization_id})
        return data.get("deleteOrganizationData", False)

    async def export_data(self, organization_id: str) -> Any:
        data = await self._t.execute(_EXPORT_DATA_MUTATION, {"organizationId": organization_id})
        return data.get("exportOrganizationData")

    async def configure_otlp(
        self, organization_id: str, endpoint: str,
        headers: dict[str, str] | None = None,
        insecure: bool | None = None,
        sample_rate: float | None = None,
    ) -> Organization:
        inp: dict[str, Any] = {"endpoint": endpoint}
        if headers is not None:
            inp["headers"] = headers
        if insecure is not None:
            inp["insecure"] = insecure
        if sample_rate is not None:
            inp["sampleRate"] = sample_rate
        data = await self._t.execute(_CONFIGURE_OTLP_MUTATION, {"organizationId": organization_id, "input": inp})
        return _parse_organization(data["configureOTLP"])

    async def disable_otlp(self, organization_id: str) -> Organization:
        data = await self._t.execute(_DISABLE_OTLP_MUTATION, {"organizationId": organization_id})
        return _parse_organization(data["disableOTLP"])
