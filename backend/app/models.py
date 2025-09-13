from pydantic import BaseModel, Field
from typing import Optional



class BusRouteProperties(BaseModel):
    ROUTE_ID: int
    ROUTE_SEQ: int
    COMPANY_CODE: Optional[str] = None
    ROUTE_NAME_E: str = Field(..., alias='ROUTE_NAMEE') # Use alias to refine irregular API field names
    ST_STOP_NAME_C: Optional[str] = Field(None, alias='ST_STOP_NAMEC')  #Starting bus stop name_Chinese_Traditional
    ST_STOP_NAME_S: Optional[str] = Field(None, alias='ST_STOP_NAMES')  #Starting bus stop name_Chinese_Simplified
    ST_STOP_NAME_E: Optional[str] = Field(None, alias='ST_STOP_NAMEE')  #Starting bus stop name_English
    ED_STOP_NAME_C: Optional[str] = Field(None, alias='ED_STOP_NAMEC')  #Terminal Bus Stop Name_Chinese_Traditional
    ED_STOP_NAME_S: Optional[str] = Field(None, alias='ED_STOP_NAMES')  #Terminal Bus Stop Name_Chinese_Simplified
    ED_STOP_NAME_E: Optional[str] = Field(None, alias='ED_STOP_NAMEE')  #Terminal Bus Stop Name_English

    class Config:
        populate_by_name = True #allow to use alias to assign the key (eg. ROUTE_NAME_E , even the key is ROUTE_NAMEE in json)