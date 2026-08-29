from app.adapters.base import BaseAdapter
from app.adapters.cisco import CiscoAdapter
from app.adapters.dell import DellAdapter
from app.adapters.hpe import HPEAdapter
from app.adapters.netscaler import NetScalerAdapter

ADAPTERS: dict[str, type[BaseAdapter]] = {
    "dell": DellAdapter,
    "cisco": CiscoAdapter,
    "netscaler": NetScalerAdapter,
    "hpe": HPEAdapter,
}

__all__ = ["BaseAdapter", "ADAPTERS"]
