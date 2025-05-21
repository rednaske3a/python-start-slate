
# ComfyUI Model Manager

A streamlined utility for downloading and managing models from Civitai for ComfyUI.

## Features

- **Simplified Model Downloads**: Easily download models from Civitai directly into the correct ComfyUI folders
- **Smart Image Management**: Automatically downloads and sorts model preview images by reaction score
- **HTML Gallery Generation**: Creates attractive HTML galleries for each downloaded model
- **Queue System**: Manage multiple downloads with priority control
- **Configurable**: Customize download behavior, concurrent downloads, and more

## Installation

1. Clone or download this repository
2. Run the installer:
```
python install.py
```
3. Follow the prompts to specify your ComfyUI installation path

## Usage

### Running the Application

Launch the application by running:
```
python path/to/comfyui/custom_nodes/ComfyUI-MM/main.py
```

### Downloading Models

1. Copy model URLs from Civitai (e.g., `https://civitai.com/models/12345/model-name`)
2. Paste URLs into the download tab (one per line)
3. Set the maximum number of images to download
4. Click "Add to Queue"

### Configuration

In the Settings tab, you can configure:
- ComfyUI installation path
- Download concurrency and threading
- Model file and image download options
- HTML gallery creation
- API key for accessing restricted content

## Generated HTML Galleries

For each downloaded model, a standalone HTML gallery is created that:
- Displays model information and metadata
- Shows preview images sorted by popularity
- Provides prompt information for each image
- Works offline (all content is local)

## License

MIT License

## Acknowledgments

- ComfyUI team for the amazing Stable Diffusion UI
- Civitai for hosting the model community
