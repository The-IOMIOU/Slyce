<!-- Copyright (c) 2026 Tiberiu Bolohan. Licensed under AGPL-3.0 -->
# Building Slyce

Slyce builds exactly like OrcaSlicer; upstream's guide is the reference:
[How to build](https://www.orcaslicer.com/wiki/developer_reference/how_to_build) (Windows, macOS, Linux).

## Windows (tested on Windows 11, Visual Studio 2026 Community, MSVC 19.51)

```bat
build_win.bat -d --vs 2026      :: dependencies (first time only; about 1–2 h, ~20 GB)
build_win.bat -s --vs 2026      :: Slyce itself
```

The app is written to `build\OrcaSlicer\` (the executable is still named `orca-slicer.exe`;
renaming it is tracked in [decision 0009](decisions/0009-fork-history-and-branding.md)).

### "SSL certificate verification failed" while downloading dependencies

If `cmake` on your `PATH` is a MinGW/WinLibs build, its curl may not have a CA bundle and every
dependency download fails with `certificate signer not trusted`. Point CMake at a CA bundle
**on a path without spaces**:

```bat
copy "C:\Program Files\Git\mingw64\etc\ssl\certs\ca-bundle.crt" C:\dev\cacert.pem
build_win.bat -d -c --vs 2026 --deps-args "-DCMAKE_TLS_CAINFO=C:/dev/cacert.pem"
```

## Running the G-code parity harness

```bash
cd tools/gcode_parity
python -m unittest discover -s tests                       # harness self-tests, no slicers needed
python -m gcode_parity.run \
  --reference "C:/Program Files/Bambu Studio/bambu-studio.exe" \
  --reference-profiles "C:/Program Files/Bambu Studio/resources/profiles" \
  --candidate build/OrcaSlicer/orca-slicer.exe \
  --candidate-profiles resources/profiles \
  --out parity-report
```

See [tools/gcode_parity/README.md](../tools/gcode_parity/README.md).
