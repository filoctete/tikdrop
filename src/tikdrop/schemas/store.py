from typing import List

from pydantic import BaseModel


class StoreCopy(BaseModel):
    """Generated marketing copy for a public product page (development_guide.pdf section 12,
    Store Generator: "títulos, benefícios, FAQs, especificações"). Advisory/generated - a human
    should review before trusting it for real customers, same as every other AI output here.
    """

    title: str
    tagline: str
    description: str
    benefits: List[str]
