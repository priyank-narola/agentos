# Agent Registry

The Agent Registry stores stable software identities and their responsible principals. Agent names are unique, but names are presentation data; the UUID is the identity used in relationships.

Agent creation requires an existing `owner_principal_id`, purpose, version, and risk classification. Lifecycle operations can suspend or retire an agent. These endpoints do not authorize agent behavior and do not authenticate callers.

The agent detail UI displays identity, owner reference, purpose, version, status, and risk. Delegations and action-request history are marked as later-phase data until their runtime workflows exist.
