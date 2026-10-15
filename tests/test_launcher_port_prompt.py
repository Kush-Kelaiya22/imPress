"""Launcher safety checks that are safe to run on the developer's machine."""

import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(os.name == "nt", reason="the POSIX launcher is not used on Windows")
def test_launcher_does_not_signal_a_listener_without_terminal_confirmation(tmp_path):
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    call_log = tmp_path / "lsof-args.txt"
    lsof = fake_bin / "lsof"
    lsof.write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "$FAKE_CALL_LOG"\nprintf "%s\\n" "$FAKE_LISTENER_PID"\n')
    lsof.chmod(0o755)

    listener = subprocess.Popen(["sleep", "30"])
    env = {
        **os.environ,
        "PATH": f"{fake_bin}:{os.environ['PATH']}",
        "FAKE_CALL_LOG": str(call_log),
        "FAKE_LISTENER_PID": str(listener.pid),
        "IMPRESS_HOST": "127.0.0.1",
        "IMPRESS_PORT": "9000",
    }
    try:
        result = subprocess.run(
            ["bash", str(ROOT / "launcher.sh")],
            input="",
            capture_output=True,
            text=True,
            env=env,
            timeout=10,
            check=False,
        )
        output = result.stdout + result.stderr
        assert result.returncode != 0
        assert "Port 8000 is already in use" in output
        assert "no process was stopped" in output
        assert "-iTCP:8000" in call_log.read_text()
        assert listener.poll() is None
    finally:
        listener.terminate()
        listener.wait(timeout=5)
