#!/usr/bin/env python3
"""Plan the bounded AV1 tile sweep or summarize saved fixtures; never run tools."""
import argparse
import json
from pathlib import Path


CASES = (("1080p120-sdr8", 1920, 1080, 120, "sdr8"),
         ("4k60-sdr8", 3840, 2160, 60, "sdr8"),
         ("4k60-hdr10", 3840, 2160, 60, "hdr10"))


def plan(args):
    commands = []
    for name, width, height, fps, variant in CASES:
        for columns in (0, 1, 2):
            output = str(Path(args.output_root) / name / f"columns{columns}-rows0")
            command = [args.fixture_tool, "--codec", "av1", "--variant", variant,
                       "--width", str(width), "--height", str(height), "--fps", str(fps),
                       "--frames", str(args.frames), "--gop", str(args.gop),
                       "--av1-tile-columns", str(columns), "--av1-tile-rows", "0",
                       "--aom-psnr", "1", "--aomenc", args.aomenc, "--output", output]
            commands.append({"case": name, "tile_columns_log2": columns,
                             "fixture": output + "/manifest.json", "command": command})
    return {"status": "PLANNED_NOT_EXECUTED", "fixed_cq_level": 12,
            "tile_rows_log2": 0, "commands": commands}


def summarize(args):
    groups = []
    for name, width, height, fps, variant in CASES:
        rows = []
        invariant = None
        for columns in (0, 1, 2):
            path = Path(args.output_root) / name / f"columns{columns}-rows0" / "manifest.json"
            manifest = json.loads(path.read_text())
            settings = manifest["generator"]["settings"]
            layout = settings["av1_layout"]
            if (manifest["codec"], manifest["width"], manifest["height"], manifest["variant"],
                manifest["frame_rate"]) != ("av1", width, height, variant, {"num": fps, "den": 1}):
                raise ValueError(f"fixture does not match planned case: {path}")
            if (layout["tile_columns_log2"], layout["tile_rows_log2"], settings["rate_control"]) != (columns, 0, {"mode": "q", "cq_level": 12}):
                raise ValueError(f"layout/CQ mismatch: {path}")
            depth = 10 if variant == "hdr10" else 8
            if (settings["width"], settings["height"], settings["fps"], settings["bit_depth"]) != (width, height, fps, depth):
                raise ValueError(f"encoder request disagrees with fixture: {path}")
            # Ignore only the layout and per-output paths in the actual arguments.
            actual = settings["actual_arguments"]
            arguments = [x for x in actual if not x.startswith(("--tile-columns=", "--output="))][:-1]
            identity = (settings["pattern"], settings["gop"], settings["frames"],
                        settings["bit_depth"], settings["encoder_version"], arguments)
            if invariant is not None and identity != invariant:
                raise ValueError(f"non-layout settings differ within case: {path}")
            invariant = identity
            quality = settings.get("quality")
            if not quality:
                raise ValueError(f"requested quality measurements unavailable: {path}")
            rows.append({"tile_columns_log2": columns,
                         "requested_columns": 1 << columns,
                         "encoded_geometry_verified": False,
                         "fixture_sha256": manifest["payload_sha256"],
                         "payload_bytes": settings["payload_bytes"],
                         "payload_bitrate_bps": settings["payload_bitrate_bps"],
                         "psnr_overall_db": quality["overall_db"],
                         "psnr_y_db": quality["y_db"],
                         "decode_latency": None})
        baseline = rows[1]
        for row in rows:
            row["bitrate_delta_percent_vs_default"] = 100 * (row["payload_bitrate_bps"] / baseline["payload_bitrate_bps"] - 1)
            row["psnr_y_delta_db_vs_default"] = row["psnr_y_db"] - baseline["psnr_y_db"]
        groups.append({"case": name, "rows": rows})
    return {"status": "SAVED_FIXTURE_QUALITY_AND_SIZE_ONLY", "groups": groups,
            "limitations": ["Fixed CQ is not fixed bitrate or equal reconstruction quality.",
                            "PSNR is encoder-reported sample-domain fidelity, not HDR perceptual quality.",
                            "Tile flags are requests; emitted geometry is not independently parsed here.",
                            "Decode latency must come from separate centrally scheduled replay measurements."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "summarize"))
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--fixture-tool", default="build/mav-fixture")
    parser.add_argument("--aomenc", default=".local/aom-build/aomenc")
    parser.add_argument("--frames", type=int, default=120)
    parser.add_argument("--gop", type=int, default=60)
    args = parser.parse_args()
    if not 3 <= args.frames <= 100000 or not 1 <= args.gop <= args.frames:
        parser.error("require 3..100000 frames and 1 <= gop <= frames")
    print(json.dumps(plan(args) if args.mode == "plan" else summarize(args), indent=2))


if __name__ == "__main__":
    main()
