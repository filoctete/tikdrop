from pydantic import BaseModel, Field


class CreativeInput(BaseModel):
    demo_video_feasibility: float = Field(ge=0, le=10, description="How easy it is to demo the benefit in a short video")
    ugc_potential: float = Field(ge=0, le=10, description="Likelihood of organic user-generated content")
