#!/bin/sh

echo -n "0000:00:14.0" | tee /sys/bus/pci/drivers/xhci_hcd/unbind
echo -n "0000:00:14.0" | tee /sys/bus/pci/drivers/xhci_hcd/bind

