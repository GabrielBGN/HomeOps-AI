"""Network change detection utilities for HomeOps-AI."""


def detect_changes(previous_device, current_device):
    """
    Compare a previously known device with the current scan result.

    Returns a list of detected network changes.

    If previous_device is None, the device is considered new.
    """

    changes = []

    # Device has never been seen before.
    if previous_device is None:
        changes.append(
            {
                "type": "new_device",
                "mac_address": current_device["mac_address"],
                "ip_address": current_device["ip_address"],
                "hostname": current_device["hostname"],
            }
        )

        return changes

    # Device changed between online and offline.
    if previous_device["status"] != current_device["status"]:
        changes.append(
            {
                "type": "status_change",
                "mac_address": current_device["mac_address"],
                "hostname": current_device["hostname"],
                "old_status": previous_device["status"],
                "new_status": current_device["status"],
            }
        )

    # Device received a different IP address.
    if previous_device["ip_address"] != current_device["ip_address"]:
        changes.append(
            {
                "type": "ip_change",
                "mac_address": current_device["mac_address"],
                "hostname": current_device["hostname"],
                "old_ip": previous_device["ip_address"],
                "new_ip": current_device["ip_address"],
            }
        )

    return changes
