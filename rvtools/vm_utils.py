"""Utility functions for VM property extraction."""


def extract_vm_template(vm):
    """Extract template status from VM config.

    Args:
        vm: pyVmomi VirtualMachine object

    Returns:
        str: "Yes" if template, "No" otherwise, empty string if unavailable
    """
    try:
        if hasattr(vm.config, "template") and vm.config.template:
            return "Yes"
        return "No"
    except Exception:
        return ""


def extract_srm_placeholder(vm):
    """Check if VM is a Site Recovery Manager placeholder.

    Detects SRM placeholder VMs by checking for SRM-specific annotations or config.

    Args:
        vm: pyVmomi VirtualMachine object

    Returns:
        str: "Yes" if SRM placeholder, "No" otherwise, empty string if unavailable
    """
    try:
        # Check for SRM-specific annotations in vm.config.annotation
        if hasattr(vm.config, "annotation") and vm.config.annotation:
            annotation = vm.config.annotation.lower()
            if "srm" in annotation or "placeholder" in annotation:
                return "Yes"

        # Check VM name pattern (SRM placeholders often have specific naming)
        if hasattr(vm, "name") and vm.name:
            name = vm.name.lower()
            if "placeholder" in name or "srm" in name:
                return "Yes"

        return "No"
    except Exception:
        return ""


def extract_custom_metadata(vm):
    """Extract custom VM metadata from annotations.

    Extracts three specific metadata keys commonly used for backup/protection:
    - com.emc.avamar.vmware.snapshot
    - com.vmware.vdp2.is-protected
    - com.vmware.vdp2.protected-by

    Args:
        vm: pyVmomi VirtualMachine object

    Returns:
        dict: Dictionary with 3 keys containing extracted metadata values
    """
    metadata = {
        "com_emc_avamar_vmware_snapshot": "",
        "com_vmware_vdp2_is_protected": "",
        "com_vmware_vdp2_protected_by": "",
    }

    try:
        if not hasattr(vm.config, "annotation") or not vm.config.annotation:
            return metadata

        annotation = vm.config.annotation

        # Parse annotation for key=value pairs (supports various delimiters)
        for line in annotation.split("\n"):
            line = line.strip()
            if not line or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()

            # Map annotation keys to our metadata keys
            if key == "com.emc.avamar.vmware.snapshot":
                metadata["com_emc_avamar_vmware_snapshot"] = value
            elif key == "com.vmware.vdp2.is-protected":
                metadata["com_vmware_vdp2_is_protected"] = value
            elif key == "com.vmware.vdp2.protected-by":
                metadata["com_vmware_vdp2_protected_by"] = value

    except Exception:
        pass

    return metadata


def extract_vm_common_properties(vm):
    """Extract all common VM properties used across multiple sheets.

    This is a convenience function that extracts all common properties at once.

    Args:
        vm: pyVmomi VirtualMachine object

    Returns:
        dict: Dictionary containing template, srm_placeholder, and metadata fields
    """
    result = {
        "template": extract_vm_template(vm),
        "srm_placeholder": extract_srm_placeholder(vm),
    }
    result.update(extract_custom_metadata(vm))
    return result
