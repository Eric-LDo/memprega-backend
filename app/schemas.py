import re
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Period(StrictModel):
    start: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    end: str = Field(default="", pattern=r"^(\d{4}-(0[1-9]|1[0-2]))?$")
    current: bool = False

    @model_validator(mode="after")
    def dates(self):
        if not self.current and not self.end:
            raise ValueError("Informe o término ou marque como atual.")
        if self.end and self.end < self.start:
            raise ValueError("O término deve ser posterior ao início.")
        if self.current:
            self.end = ""
        return self


class Experience(Period):
    role: str = Field(min_length=2, max_length=160)
    company: str = Field(min_length=2, max_length=160)
    description: str = Field(default="", max_length=4000)


class Education(Period):
    course: str = Field(min_length=2, max_length=160)
    institution: str = Field(min_length=2, max_length=160)
    level: str = Field(min_length=2, max_length=80)


class Language(StrictModel):
    name: str = Field(min_length=2, max_length=80)
    level: str = Field(pattern=r"^(Básico|Intermediário|Avançado|Fluente|Nativo)$")


class ResumeData(StrictModel):
    name: str = Field(min_length=2, max_length=160)
    email: EmailStr = Field(max_length=254)
    phone: str = Field(min_length=8, max_length=30)
    city: str = Field(min_length=2, max_length=120)
    title: str = Field(min_length=2, max_length=160)
    summary: str = Field(default="", max_length=4000)
    linkedin: str = Field(default="", max_length=300)
    portfolio: str = Field(default="", max_length=300)
    experiences: list[Experience] = Field(default_factory=list, max_length=20)
    education: list[Education] = Field(default_factory=list, max_length=20)
    skills: list[str] = Field(default_factory=list, max_length=40)
    languages: list[Language] = Field(default_factory=list, max_length=15)

    @field_validator("linkedin", "portfolio")
    @classmethod
    def safe_url(cls, value):
        if value and not re.match(r"^https?://[^\s/]+", value):
            raise ValueError("Use um endereço iniciado por https:// ou http://.")
        return value

    @field_validator("skills")
    @classmethod
    def skills_length(cls, values):
        if any(not v.strip() or len(v) > 80 for v in values):
            raise ValueError("Cada habilidade deve ter entre 1 e 80 caracteres.")
        return list(dict.fromkeys(v.strip() for v in values))
