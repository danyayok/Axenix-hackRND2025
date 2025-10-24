from typing import List, Optional, Union
from pydantic import BaseModel

class RTCIceServer(BaseModel):
    urls: Union[str, List[str]]
    username: Optional[str] = None
    credential: Optional[str] = None

class RTCConfigOut(BaseModel):
    iceServers: List[RTCIceServer]
