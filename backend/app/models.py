from pydantic import BaseModel, Field
from typing import Optional

# according to KMB API doc (kmb_eta_data_dictionary.pdf, 2.1 Route / Route List) to build data model
class KmbBusRoute(BaseModel):
    co: Optional[str] = None
    route: str
    bound: str
    service_type: str = Field(..., alias='service_type')
    orig_en: Optional[str] = None
    orig_tc: Optional[str] = None
    orig_sc: Optional[str] = None
    dest_en: Optional[str] = None
    dest_tc: Optional[str] = None
    dest_sc: Optional[str] = None

    class Config:
        populate_by_name = True # allow alias