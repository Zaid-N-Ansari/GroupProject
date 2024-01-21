from enum import Enum

class FriendReqStatus(Enum):
	NO_REQ_SENT = 1
	SENT_TO_YOU = 2
	YOU_SENT_THEM = 3