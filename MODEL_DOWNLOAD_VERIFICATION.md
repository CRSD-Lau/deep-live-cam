# Model Download Verification

Generated: 2026-05-18

This records a local verification run of the explicit model downloader. It is release evidence only and is not permission to redistribute the model files.

## Command

```powershell
$env:DLC_MODELS_DIR = "C:\Users\neil_\AppData\Local\Temp\DeepLiveCamStudio-real-model-download-1469c940687d44ec91e4a95462161a46"
venv\Scripts\python.exe run.py --download-models --yes
```

Exit code: `0`

## Verified Downloads

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `inswapper_128.onnx` | 554253681 | `E4A3F08C753CB72D04E10AA0F7DBE3DEEBBF39567D4EAD6DCE08E98AA49E16AF` |
| `inswapper_128_fp16.onnx` | 277680638 | `6D51A9278A1F650CFFEFC18BA53F38BF2769BF4BBFF89267822CF72945F8A38B` |
| `GPEN-BFR-256.onnx` | 75715262 | `AA5BD3AB238640A378C59E4A560F7A7150627944CF2129E6311AE4720E833271` |
| `GPEN-BFR-512.onnx` | 284250449 | `0960F836488735444D508B588E44FB5DFD19C68FDE9163AD7878AA24D1D5115E` |
| `gfpgan-1024.onnx` | 365875079 | `EE8DD6415E388B3A410689D5D9395A2BF50B5973B588421EBFA57BC266F19E24` |

## Containment

- The download used `DLC_MODELS_DIR` so model files were written outside the repository and outside the installer payload.
- Repository scan for `*.onnx`, `*.pth`, `*.safetensors`, `models/**`, and `checkpoints/**` returned no entries.
- Packaged dist scan under `dist\DeepLiveCamStudio` returned no `*.onnx`, `*.pth`, or `*.safetensors` files.
- The temporary model download directory was deleted after verification.

## Remaining Model Gates

- This proves that the downloader can fetch the currently configured model URLs and verify checksums in this environment.
- This does not prove model redistribution rights.
- This does not replace CPU/CUDA processing tests with the downloaded models.
