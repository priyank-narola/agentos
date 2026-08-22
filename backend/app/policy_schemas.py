from pydantic import Field

from app.schemas import PolicyRuleSchema, PolicySchema


class PolicyRuleResponse(PolicyRuleSchema):
    pass


class PolicyDetailSchema(PolicySchema):
    rules: list[PolicyRuleResponse] = Field(default_factory=list)
