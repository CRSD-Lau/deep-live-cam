<h1 align="center">Deep-Live-Cam 2.1.5</h1>

<p align="center">
  Real-time face swap and video deepfake with a single click and only a single image.
</p>

<p align="center">
<a href="https://trendshift.io/repositories/11395" target="_blank"><img src="https://trendshift.io/api/badge/repositories/11395" alt="hacksider%2FDeep-Live-Cam | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/></a>
</p>

<p align="center">
  <img src="media/demo.gif" alt="Demo GIF" width="800">
</p>

##  Disclaimer

This deepfake software is designed to be a productive tool for the AI-generated media industry. It can assist artists in animating custom characters, creating engaging content, and even using models for clothing design.

We are aware of the potential for unethical applications and are committed to preventative measures. A built-in check prevents the program from processing inappropriate media (nudity, graphic content, sensitive material like war footage, etc.). We will continue to develop this project responsibly, adhering to the law and ethics. We may shut down the project or add watermarks if legally required.

- Ethical Use: Users are expected to use this software responsibly and legally. If using a real person's face, obtain their consent and clearly label any output as a deepfake when sharing online.

- Content Restrictions: The software includes built-in checks to prevent processing inappropriate media, such as nudity, graphic content, or sensitive material.

- Legal Compliance: We adhere to all relevant laws and ethical guidelines. If legally required, we may shut down the project or add watermarks to the output.

- User Responsibility: We are not responsible for end-user actions. Users must ensure their use of the software aligns with ethical standards and legal requirements.

By using this software, you agree to these terms and commit to using it in a manner that respects the rights and dignity of others.

Users are expected to use this software responsibly and legally. If using a real person's face, obtain their consent and clearly label any output as a deepfake when sharing online. We are not responsible for end-user actions.

## Exclusive v2.7 beta Quick Start - Pre-built (Windows/Mac Silicon/CPU)

  <a href="https://deeplivecam.net/index.php/quickstart"> <img src="media/Download.png" width="285" height="77" />

##### This is the fastest build you can get if you have a discrete NVIDIA or AMD GPU, CPU or Mac Silicon, And you'll receive special priority support. 2.7 beta is the best you can have with 30+ extra features than the open source version.
 
###### These Pre-builts are perfect for non-technical users or those who don't have time to, or can't manually install all the requirements. Just a heads-up: this is an open-source project, so you can also install it manually. 

## TLDR; Live Deepfake in just 3 Clicks
![easysteps](https://github.com/user-attachments/assets/af825228-852c-411b-b787-ffd9aac72fc6)
1. Select a face
2. Select which camera to use
3. Press live!

## Features & Uses - Everything is in real-time

### Mouth Mask

**Retain your original mouth for accurate movement using Mouth Mask**

<p align="center">
  <img src="media/ludwig.gif" alt="resizable-gif">
</p>

### Face Mapping

**Use different faces on multiple subjects simultaneously**

<p align="center">
  <img src="media/streamers.gif" alt="face_mapping_source">
</p>

### Your Movie, Your Face

**Watch movies with any face in real-time**

<p align="center">
  <img src="media/movie.gif" alt="movie">
</p>

### Live Show

**Run Live shows and performances**

<p align="center">
  <img src="media/live_show.gif" alt="show">
</p>

### Memes

**Create Your Most Viral Meme Yet**

<p align="center">
  <img src="media/meme.gif" alt="show" width="450"> 
  <br>
  <sub>Created using Many Faces feature in Deep-Live-Cam</sub>
</p>

### Omegle

**Surprise people on Omegle**

<p align="center">
  <video src="https://github.com/user-attachments/assets/2e9b9b82-fa04-4b70-9f56-b1f68e7672d0" width="450" controls></video>
</p>

## Installation (Manual)

**Please be aware that the installation requires technical skills and is not for beginners. Consider downloading the quickstart version.**

<details>
<summary>Click to see the process</summary>

### Installation

This is more likely to work on your computer but will be slower as it utilizes the CPU.

**1. Set up Your Platform**

-   Python (3.11 recommended)
-   pip
-   git
-   [ffmpeg](https://www.youtube.com/watch?v=OlNWCpFdVMA) - ```iex (irm ffmpeg.tc.ht)```
-   [Visual Studio 2022 Runtimes (Windows)](https://visualstudio.microsoft.com/visual-cpp-build-tools/)

**2. Clone the Repository**

```bash
git clone https://github.com/hacksider/Deep-Live-Cam.git
cd Deep-Live-Cam
```

**3. Download the Models**

1. [gfpgan-1024.onnx](https://huggingface.co/hacksider/deep-live-cam/resolve/main/gfpgan-1024.onnx)
2. [inswapper\_128\_fp16.onnx](https://huggingface.co/hacksider/deep-live-cam/resolve/main/inswapper_128_fp16.onnx)

Review the model license notes before downloading. For source checkouts, place reviewed files in the "**models**" folder, or run:

```bash
python run.py --download-models
```

**4. Install Dependencies**

We highly recommend using a `venv` to avoid issues.


For Windows:
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```
For Linux:
```bash
# Ensure you use the installed Python 3.11
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**For macOS:**

Apple Silicon (M1/M2/M3) requires specific setup:

```bash
# Install Python 3.11 (specific version is important)
brew install python@3.11

# Install tkinter package (required for the GUI)
brew install python-tk@3.11

# Create and activate virtual environment with Python 3.11
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

** In case something goes wrong and you need to reinstall the virtual environment **

```bash
# Deactivate the virtual environment
rm -rf venv

# Reinstall the virtual environment
python -m venv venv
source venv/bin/activate

# install the dependencies again
pip install -r requirements.txt

# gfpgan and basicsrs issue fix
pip install git+https://github.com/xinntao/BasicSR.git@master
pip uninstall gfpgan -y
pip install git+https://github.com/TencentARC/GFPGAN.git@master
```

**Run:** If you don't have a GPU, you can run Deep-Live-Cam using `python run.py`. Model download is explicit; run `python run.py --download-models` first or place reviewed models in the configured model folder.

### Windows Clickable Desktop App

After dependencies are installed, create a no-console desktop shortcut:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\install_windows_desktop_app.ps1
```

This adds **Deep Live Cam Studio** to your Windows Desktop. The shortcut launches
`DeepLiveCamStudio.pyw` with `venv\Scripts\pythonw.exe` when the local virtual
environment exists, so the native PySide studio opens without a command prompt.
Desktop startup logs are written to `runtime\desktop-launch.log`.

The command-line entry point remains available for benchmarking, diagnostics,
OBS virtual camera flags, and explicit provider selection:

```bash
python run.py --execution-provider cuda
```

### GPU Acceleration

**CUDA Execution Provider (Nvidia)**

1. Install a current NVIDIA driver.
2. Install dependencies:

```bash
pip install -U torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
pip uninstall onnxruntime onnxruntime-gpu
pip install onnxruntime-gpu==1.23.2
```

The CUDA-enabled PyTorch wheel supplies the CUDA 12/cuDNN 9 DLLs that
`onnxruntime-gpu==1.23.2` needs on Windows. To verify that CUDA really loads for
an ONNX session:

```bash
python tools/check_cuda_provider.py --execution-provider cuda --strict
```

3. Usage:

```bash
python run.py --execution-provider cuda
```

**CoreML Execution Provider (Apple Silicon)**

Apple Silicon (M1/M2/M3) specific installation:

1. Make sure you've completed the macOS setup above using Python 3.11.
2. Install dependencies:

```bash
pip uninstall onnxruntime onnxruntime-silicon
pip install onnxruntime-silicon==1.13.1
```

3. Usage:

```bash
python3.11 run.py --execution-provider coreml
```

**Important Notes for macOS:**
- You **must** use Python 3.11, not newer versions like 3.13
- Always run with `python3.11` command not just `python` if you have multiple Python versions installed
- If you get error about `_tkinter` missing, reinstall the tkinter package: `brew reinstall python-tk@3.11`
- If you get model loading errors, check that your models are in the correct folder
- If you encounter conflicts with other Python versions, consider uninstalling them:
  ```bash
  # List all installed Python versions
  brew list | grep python

  # Uninstall conflicting versions if needed
  brew uninstall --ignore-dependencies python@3.13

  # Keep only Python 3.11
  brew cleanup
  ```

**CoreML Execution Provider (Apple Legacy)**

1. Install dependencies:

```bash
pip uninstall onnxruntime onnxruntime-coreml
pip install onnxruntime-coreml==1.21.0
```

2. Usage:

```bash
python run.py --execution-provider coreml
```

**DirectML Execution Provider (Windows)**

1. Install dependencies:

```bash
pip uninstall onnxruntime onnxruntime-directml
pip install onnxruntime-directml==1.21.0
```

2. Usage:

```bash
python run.py --execution-provider directml
```

**OpenVINO™ Execution Provider (Intel)**

1. Install dependencies:

```bash
pip uninstall onnxruntime onnxruntime-openvino
pip install onnxruntime-openvino==1.21.0
```

2. Usage:

```bash
python run.py --execution-provider openvino
```
</details>

## Usage

**1. Image/Video Mode**

-   Execute `python run.py`.
-   Choose a source face image and a target image/video.
-   Click "Start".
-   The output will be saved in a directory named after the target video.

**2. Webcam Mode**

-   Execute `python run.py`.
-   Select a source face image.
-   Click "Live".
-   Wait for the preview to appear (10-30 seconds).
-   Use a screen capture tool like OBS to stream.
-   To change the face, select a new source image.

**3. Windows OBS Virtual Camera Mode**

Deep-Live-Cam can send the processed live output directly to a virtual camera:

```bash
python run.py --execution-provider cuda --virtual-cam
```

The default virtual camera output is `1280x720@30`. Optional settings:

```bash
python run.py --execution-provider cuda --virtual-cam --virtual-cam-name "OBS Virtual Camera" --virtual-cam-width 1280 --virtual-cam-height 720 --virtual-cam-fps 30
```

For higher-FPS streaming, keep the model processing resolution separate from
the virtual camera signal. This processes at `720p60` and publishes a
`1080p60` virtual camera stream:

```bash
python run.py --execution-provider cuda --virtual-cam --camera-width 1280 --camera-height 720 --camera-fps 60 --virtual-cam-width 1920 --virtual-cam-height 1080 --virtual-cam-fps 60
```

OBS's built-in virtual camera is a single device. Use direct virtual camera
output for Discord/Zoom/Teams, or use OBS Window Capture on the
`Deep-Live-Cam Live Preview` window when you need OBS to rebroadcast the scene.
See [docs/OBS_VIRTUAL_CAMERA.md](docs/OBS_VIRTUAL_CAMERA.md) for setup,
diagnostics, and troubleshooting.

## Model download and license review

Models are not bundled with Windows installers by default. Use `python run.py --download-models` from source checkouts or `DeepLiveCamStudioCLI.exe --download-models` from installed builds to review model sources, license notes, and SHA-256 checksums before download. Do not upload model binaries to GitHub Releases unless redistribution rights are confirmed for each file.

## Command Line Arguments (Unmaintained)

```
options:
  -h, --help                                               show this help message and exit
  -s SOURCE_PATH, --source SOURCE_PATH                     select a source image
  -t TARGET_PATH, --target TARGET_PATH                     select a target image or video
  -o OUTPUT_PATH, --output OUTPUT_PATH                     select output file or directory
  --frame-processor FRAME_PROCESSOR [FRAME_PROCESSOR ...]  frame processors (choices: face_swapper, face_enhancer, ...)
  --keep-fps                                               keep original fps
  --keep-audio                                             keep original audio
  --keep-frames                                            keep temporary frames
  --many-faces                                             process every face
  --map-faces                                              map source target faces
  --mouth-mask                                             mask the mouth region
  --video-encoder {libx264,libx265,libvpx-vp9}             adjust output video encoder
  --video-quality [0-51]                                   adjust output video quality
  --live-mirror                                            the live camera display as you see it in the front-facing camera frame
  --live-resizable                                         the live camera frame is resizable
  --camera-width CAMERA_WIDTH                              live camera capture width
  --camera-height CAMERA_HEIGHT                            live camera capture height
  --camera-fps CAMERA_FPS                                  live camera capture fps
  --virtual-cam                                            send processed live preview frames to a virtual camera
  --virtual-cam-name VIRTUAL_CAM_NAME                      virtual camera device name to use
  --virtual-cam-width VIRTUAL_CAM_WIDTH                    virtual camera output width
  --virtual-cam-height VIRTUAL_CAM_HEIGHT                  virtual camera output height
  --virtual-cam-fps VIRTUAL_CAM_FPS                        virtual camera output fps
  --max-memory MAX_MEMORY                                  maximum amount of RAM in GB
  --execution-provider PROVIDER [PROVIDER ...]             execution provider (cuda, directml, dml, cpu, ...)
  --execution-threads EXECUTION_THREADS                    number of execution threads
  -v, --version                                            show program's version number and exit
```

Looking for a CLI mode? Using the -s/--source argument will make the run program in cli mode.

## Windows installer builds

This repository includes a Windows packaging flow for GitHub Releases. It builds a PyInstaller application bundle and wraps it with an Inno Setup per-user installer.

Run the standard local release gate:

```powershell
powershell -ExecutionPolicy Bypass -File build\windows\run_release_checks.ps1 -AppVersion 2.1.5 -GitRef <release-tag-or-commit>
```

The GitHub Actions workflow in `.github/workflows/windows-release.yml` runs the same release gate and uploads the installer, installer hash, corresponding-source archive, and source hash.
The gate also writes `RELEASE_VERIFICATION.md`, which summarizes the installer hash, payload manifest status, source-archive status, and manual gates that still need human confirmation.

Build the application bundle:

```powershell
powershell -ExecutionPolicy Bypass -File build\windows\build_windows.ps1
```

Run local preflight checks:

```powershell
powershell -ExecutionPolicy Bypass -File build\windows\test_packaged_runtime.ps1
powershell -ExecutionPolicy Bypass -File build\windows\test_environment.ps1
```

Package the installer:

```powershell
powershell -ExecutionPolicy Bypass -File build\windows\package_installer.ps1 -AppVersion 2.1.5
```

Package the corresponding source archive for the exact release tag or commit:

```powershell
powershell -ExecutionPolicy Bypass -File build\windows\package_source.ps1 -AppVersion 2.1.5 -GitRef <release-tag-or-commit>
```

The source archive script refuses a dirty working tree by default, verifies required AGPL/compliance/build files are present in the selected Git ref, and rejects model/checkpoint entries.
It also writes a `.manifest.md` beside the source zip with the resolved commit, archive hash, required-entry checks, and forbidden model/checkpoint scan result.
Before running it for a public release, commit the generated release evidence files such as `LICENSES\PYTHON_DEPENDENCIES.md`, `LICENSES\THIRD_PARTY_LICENSES\`, and `LICENSES\WINDOWS_BUNDLE_MANIFEST.md`; `-AllowDirty` is only for CI/local diagnostics and does not include uncommitted files in the source archive.
For a draft installer built from a dirty local workspace, you can create a traceability-only worktree source archive:

```powershell
powershell -ExecutionPolicy Bypass -File build\windows\package_source.ps1 -AppVersion 2.1.5 -FromWorkingTree
```

Do not use a `draft-working-tree` source archive for a public GitHub Release; tag or commit the release and rerun the clean Git ref command above.

The installer output is:

```text
build\windows\installer\DeepLiveCamStudio-2.1.5-x64-setup.exe
```

The build also generates `LICENSES\WINDOWS_BUNDLE_MANIFEST.md` from the actual PyInstaller payload and includes it in the installer for release auditing. Bundled LGPL/GPL-family binary obligations are summarized in `LICENSES\BUNDLED_BINARY_OBLIGATIONS.md`, and high-attention package license files are collected under `LICENSES\THIRD_PARTY_LICENSES\`, including TensorFlow, ONNX Runtime, OpenCV, Qt/PySide, pyvirtualcam, and model-safety dependencies. The release gate prunes known dependency sample/test folders from the PyInstaller payload and records that scan in the bundle manifest. Model redistribution notes live in `LICENSES\MODEL_LICENSE_AUDIT.md` and should be rechecked before every public release.
After the release gate completes, review `RELEASE_VERIFICATION.md` before publishing.

The default install path is versioned and per-user:

```text
%LOCALAPPDATA%\Programs\DeepLiveCamStudio\2.1.5
```

### Model setup for installed builds

The Windows installer does not bundle model files. This is intentional: model repositories can have licenses and use restrictions separate from AGPL-3.0, including GPL-3.0 and non-commercial research restrictions.

After installing, run:

```powershell
DeepLiveCamStudioCLI.exe --download-models
```

The downloader shows the model source URLs, license notes, and SHA-256 checksums before downloading. Models are stored in:

```text
%LOCALAPPDATA%\DeepLiveCamStudio\models
```

Use `DLC_MODELS_DIR` to point the app at a different reviewed model folder.

### Windows runtime notes

- ffmpeg and ffprobe are required for video processing and audio restore. This installer does not bundle ffmpeg by default. Install ffmpeg separately or place `ffmpeg.exe` and `ffprobe.exe` beside `DeepLiveCamStudio.exe`.
- CUDA acceleration requires compatible NVIDIA drivers and CUDA/cuDNN runtime libraries for `onnxruntime-gpu`. If CUDA is unavailable, use CPU or DirectML where supported.
- OBS Virtual Camera is optional and must be installed/configured through OBS. Start the OBS virtual camera before selecting virtual camera output in the app.
- Desktop launch logs are written to `%LOCALAPPDATA%\DeepLiveCamStudio\logs`.
- UI switch state is written to `%LOCALAPPDATA%\DeepLiveCamStudio\switch_states.json`.

### Uninstall

The uninstaller removes application files. It asks before deleting downloaded models under `%LOCALAPPDATA%\DeepLiveCamStudio\models`.

### License and source obligations

Deep-Live-Cam is AGPL-3.0. If you distribute a Windows installer or executable, publish the complete corresponding source for the exact binary release, including packaging scripts and modifications. Include `LICENSE`, `THIRD_PARTY_NOTICES.md`, `COMPLIANCE.md`, `LICENSES\BUNDLED_BINARY_OBLIGATIONS.md`, `LICENSES\THIRD_PARTY_LICENSES\`, and a link to the exact source tag or commit in the GitHub Release.

## Press

 - [**Ars Technica**](https://arstechnica.com/information-technology/2024/08/new-ai-tool-enables-real-time-face-swapping-on-webcams-raising-fraud-concerns/) - *"Deep-Live-Cam goes viral, allowing anyone to become a digital doppelganger"*
 - [**Yahoo!**](https://www.yahoo.com/tech/ok-viral-ai-live-stream-080041056.html) - *"OK, this viral AI live stream software is truly terrifying"*
 - [**CNN Brasil**](https://www.cnnbrasil.com.br/tecnologia/ia-consegue-clonar-rostos-na-webcam-entenda-funcionamento/) - *"AI can clone faces on webcam; understand how it works"*
 - [**Bloomberg Technoz**](https://www.bloombergtechnoz.com/detail-news/71032/kenalan-dengan-teknologi-deep-live-cam-bisa-jadi-alat-menipu) - *"Get to know Deep Live Cam technology, it can be used as a tool for deception."*
 - [**TrendMicro**](https://www.trendmicro.com/vinfo/gb/security/news/cyber-attacks/ai-vs-ai-deepfakes-and-ekyc) - *"AI vs AI: DeepFakes and eKYC"*
 - [**PetaPixel**](https://petapixel.com/2024/08/14/deep-live-cam-deepfake-ai-tool-lets-you-become-anyone-in-a-video-call-with-single-photo-mark-zuckerberg-jd-vance-elon-musk/) - *"Deepfake AI Tool Lets You Become Anyone in a Video Call With Single Photo"*
 - [**SomeOrdinaryGamers**](https://www.youtube.com/watch?time_continue=1074&v=py4Tc-Y8BcY) - *"That's Crazy, Oh God. That's Fucking Freaky Dude... That's So Wild Dude"*
 - [**IShowSpeed**](https://www.youtube.com/live/mFsCe7AIxq8?feature=shared&t=2686) - *"Alright look look look, now look chat, we can do any face we want to look like chat"*
 - [**TechLinked (Linus Tech Tips)**](https://www.youtube.com/watch?v=wnCghLjqv3s&t=551s) - *"They do a pretty good job matching poses, expression and even the lighting"*
 - [**IShowSpeed**](https://youtu.be/JbUPRmXRUtE?t=3964) - *"What the F***! Why do I look like Vinny Jr? I look exactly like Vinny Jr!? No, this shit is crazy! Bro This is F*** Crazy!"*


## Credits

-   [ffmpeg](https://ffmpeg.org/): for making video-related operations easy
-   [Henry](https://github.com/henryruhs): One of the major contributor in this repo
-   [deepinsight](https://github.com/deepinsight): for their [insightface](https://github.com/deepinsight/insightface) project which provided a well-made library and models. Please be reminded that the [use of the model is for non-commercial research purposes only](https://github.com/deepinsight/insightface?tab=readme-ov-file#license).
-   [havok2-htwo](https://github.com/havok2-htwo): for sharing the code for webcam
-   [GosuDRM](https://github.com/GosuDRM): for the open version of roop
-   [pereiraroland26](https://github.com/pereiraroland26): Multiple faces support
-   [vic4key](https://github.com/vic4key): For supporting/contributing to this project
-   [kier007](https://github.com/kier007): for improving the user experience
-   [qitianai](https://github.com/qitianai): for multi-lingual support
-   [laurigates](https://github.com/laurigates): Decoupling stuffs to make everything faster!
-   [maxwbuckley](https://github.com/maxwbuckley): For making the effort to optimize this for mac!
-   and [all developers](https://github.com/hacksider/Deep-Live-Cam/graphs/contributors) behind libraries used in this project.
-   Footnote: Please be informed that the base author of the code is [s0md3v](https://github.com/s0md3v/roop)
-   All the wonderful users who helped make this project go viral by starring the repo ❤️

[![Stargazers](https://reporoster.com/stars/hacksider/Deep-Live-Cam)](https://github.com/hacksider/Deep-Live-Cam/stargazers)

## Contributions

![Alt](https://repobeats.axiom.co/api/embed/fec8e29c45dfdb9c5916f3a7830e1249308d20e1.svg "Repobeats analytics image")

## Stars to the Moon 🚀

<a href="https://star-history.com/#hacksider/deep-live-cam&Date">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=hacksider/deep-live-cam&type=Date&theme=dark" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=hacksider/deep-live-cam&type=Date" />
   <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=hacksider/deep-live-cam&type=Date" />
 </picture>
</a>
