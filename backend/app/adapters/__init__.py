from app.adapters.base import BaseAdapter
from app.adapters.cisco import CiscoAdapter
from app.adapters.dell import DellAdapter
from app.adapters.f5 import F5Adapter
from app.adapters.fortinet import FortinetAdapter
from app.adapters.hpe import HPEAdapter
from app.adapters.netscaler import NetScalerAdapter
from app.adapters.paloalto import PaloAltoAdapter
from app.adapters.vmware import VMwareAdapter

ADAPTERS: dict[str, type[BaseAdapter]] = {
    "dell": DellAdapter,
    "cisco": CiscoAdapter,
    "netscaler": NetScalerAdapter,
    "hpe": HPEAdapter,
    "vmware": VMwareAdapter,
    "paloalto": PaloAltoAdapter,
    "fortinet": FortinetAdapter,
    "f5": F5Adapter,
}

__all__ = ["BaseAdapter", "ADAPTERS"]
