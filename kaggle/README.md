# Kaggle notebook commands

This directory contains the code intended for Kaggle notebook execution.

## Copy/paste rule

Do not paste multiline Python implementations into Kaggle cells. Pull the repository, then run a committed script with a one-line cell. This avoids indentation damage during copy/paste and keeps notebook logic version-controlled.

## Current next command

```python
!python kaggle/01_verify_stack.py
```

## Standard update command

Run this only when Codex says a new script or code change was pushed:

```python
!git pull
```

`git pull` is not required between cells when the relevant script was already present in the current clone.

