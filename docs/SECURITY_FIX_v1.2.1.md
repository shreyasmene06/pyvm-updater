# Security Fix Documentation (v1.2.1)

This document describes the critical security issue fixed in version 1.2.1 and provides recovery instructions for affected users.

## Summary

Version 1.2.0 and earlier contained code that could freeze Linux systems by modifying the system Python symlink. Version 1.2.1 and later are safe and only install Python side-by-side without modifying system defaults.

## The Problem

### What Happened

The `pyvm set-default` command and `--set-default` flag used `update-alternatives` to modify `/usr/bin/python3`, which is the system Python symlink. Many Linux system tools depend on the system Python version, and changing it caused:

- Terminal freezes
- Package manager failures (apt, dnf, yum)
- System settings application crashes
- GUI tool failures
- Cascade failures across the system

### Why It Was Dangerous

1. System Python is critical infrastructure on Linux
2. Many system tools hardcode the expected Python version
3. Changing the symlink breaks compatibility
4. Recovery requires boot into recovery mode or live USB

## The Fix

### Code Removed

- `_set_python_default_linux()` function
- `prompt_set_as_default()` function
- `pyvm set-default` CLI command
- `--set-default` flag from update command

### Current Behavior

The tool now:

1. Installs Python versions side-by-side
2. Never modifies system Python
3. Never changes symlinks
4. Never uses `update-alternatives` automatically
5. Provides instructions for using the new version

## Recovery Instructions

If your system was affected by version 1.2.0, follow these steps.

### Option 1: Recovery Mode

1. Restart your computer
2. Hold Shift during boot to access GRUB menu
3. Select "Advanced options" then "Recovery mode"
4. Select "root - Drop to root shell prompt"
5. Run:

```bash
update-alternatives --set python3 /usr/bin/python3.10
```

Replace `3.10` with your original Python version.

6. Reboot:

```bash
reboot
```

### Option 2: Live USB

1. Boot from Ubuntu/Debian live USB
2. Mount your system partition:

```bash
sudo mount /dev/sda1 /mnt
# Adjust device name as needed
```

3. Chroot into the system:

```bash
sudo chroot /mnt
```

4. Fix the symlink:

```bash
update-alternatives --set python3 /usr/bin/python3.10
# Or manually:
ln -sf /usr/bin/python3.10 /usr/bin/python3
```

5. Exit and reboot:

```bash
exit
sudo reboot
```

### Option 3: If Terminal Works

If you can access a terminal (even if frozen), try:

```bash
# Check available versions
ls /usr/bin/python3*

# Restore original
sudo ln -sf /usr/bin/python3.10 /usr/bin/python3
```

## Verification

After recovery, verify your system:

```bash
# Check Python version
python3 --version

# Check package manager
apt update

# Check alternatives
update-alternatives --display python3
```

## Prevention

To safely use multiple Python versions:

### Virtual Environments (Recommended)

```bash
python3.12 -m venv myproject
source myproject/bin/activate
python --version  # Shows 3.12 in this environment only
```

### Direct Invocation

```bash
python3.12 your_script.py
python3.12 -m pip install package_name
```

### pyenv (For Advanced Users)

```bash
# Install pyenv
curl https://pyenv.run | bash

# Install and use a version
pyenv install 3.12.0
pyenv local 3.12.0
```

## Updating to Safe Version

```bash
cd pyvm-updater
git pull
pip install --user .
pyvm --version
# Should show 2.2.0 or later
```

## Contact

If you encounter issues or need assistance, open an issue on the GitHub repository.
