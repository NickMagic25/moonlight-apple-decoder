#!/usr/bin/env python3
"""Check fixture layout planning and rejection without launching any encoder."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import importlib.util
from types import SimpleNamespace

tool = str(Path(sys.argv[1]).resolve())
with tempfile.TemporaryDirectory(prefix="mav-fixture-options-", dir=Path(tool).parent) as temp:
    root = Path(temp)
    def run(name, flags=(), success=True):
        output = root / name
        command = [tool, "--output", str(output), "--plan-only", "1", "--aomenc", "/encoder-must-not-run", *flags]
        result = subprocess.run(command, text=True, capture_output=True)
        assert (result.returncode == 0) == success, result.stderr
        assert not (output / "source.yuv").exists()
        assert not (output / "payload.bin").exists()
        return json.loads((output / "encoder-settings.json").read_text()) if success else None

    default = run("default")
    assert default["actual_arguments"] is None
    assert default["rate_control"] == {"mode": "q", "cq_level": 12}
    assert "--tile-columns=1" in default["planned_arguments"]
    assert not any(x.startswith(("--tile-rows=", "--psnr=")) for x in default["planned_arguments"])
    for columns in (0, 1, 2):
        settings = run(f"columns{columns}", ["--av1-tile-columns", str(columns), "--av1-tile-rows", "0", "--aom-psnr", "1"])
        assert settings["av1_layout"]["tile_columns_log2"] == columns
        assert f"--tile-columns={columns}" in settings["planned_arguments"]
        assert "--tile-rows=0" in settings["planned_arguments"]
        assert "--psnr=1" in settings["planned_arguments"]
    rows = run("rows", ["--av1-tile-rows", "2"])
    assert "--tile-rows=2" in rows["planned_arguments"]
    for name, flags in (("negative", ["--av1-tile-columns", "-1"]),
                        ("overflow", ["--av1-tile-columns", "7"]),
                        ("suffix", ["--av1-tile-rows", "1x"]),
                        ("hevc", ["--codec", "hevc", "--av1-tile-columns", "1"]),
                        ("unknown", ["--hevc-slices", "2"]),
                        ("import", ["--import", "/must-not-read", "--av1-tile-columns", "0"])):
        run(name, flags, success=False)
    spec = importlib.util.spec_from_file_location("encoder_layout", Path(__file__).resolve().parents[1] / "scripts/encoder-layout.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    args = SimpleNamespace(output_root=str(root / "summary-input"), fixture_tool=tool,
                           aomenc="/encoder-must-not-run", frames=120, gop=60)
    planned = module.plan(args)
    assert len(planned["commands"]) == 9
    # Artificial JSON only: validate calculations and rejection, not encode results.
    for item in planned["commands"]:
        command = item["command"]
        options = dict(zip(command[1::2], command[2::2]))
        columns = item["tile_columns_log2"]
        source = run("summary-" + item["case"] + str(columns), ["--av1-tile-columns", str(columns), "--av1-tile-rows", "0", "--aom-psnr", "1", "--width", options["--width"], "--height", options["--height"], "--variant", options["--variant"], "--fps", options["--fps"]])
        source.update(actual_arguments=source["planned_arguments"], encoder_version="synthetic-test-data", payload_bytes=1000,
                      payload_bitrate_bps=1000 * (columns + 1), quality={"overall_db":40 + columns, "y_db":38 + columns})
        manifest = {"codec":"av1", "width":int(options["--width"]), "height":int(options["--height"]),
                    "variant":options["--variant"], "frame_rate":{"num":int(options["--fps"]), "den":1},
                    "payload_sha256":"synthetic-test-data", "generator":{"settings":source}}
        path = Path(item["fixture"])
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(manifest))
    summary = module.summarize(args)
    assert summary["groups"][0]["rows"][0]["bitrate_delta_percent_vs_default"] == -50
    assert summary["groups"][0]["rows"][2]["psnr_y_delta_db_vs_default"] == 1
    path = Path(planned["commands"][2]["fixture"])
    bad = json.loads(path.read_text())
    bad["generator"]["settings"]["gop"] = 30
    path.write_text(json.dumps(bad))
    try:
        module.summarize(args)
        raise AssertionError("mismatched GOP was accepted")
    except ValueError:
        pass
print("PASS fixture argument defaults, layout planning/rejection, and report comparison guards; no encoder launched")
