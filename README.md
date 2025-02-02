# ImageArtificer

`ImageArtificer` is a powerful Python utility for **loading, processing, and enhancing images**. Just like a skilled artisan, it helps you transform raw images into polished visuals while maintaining clarity and composition.

## Features
With `ImageArtificer`, you can:

- **Load Images**: Import images from local storage, URLs, Google Cloud Storage, or Google Search.
- **Scale & Pad**: Resize images while maintaining aspect ratio, with optional padding using dominant or complementary colors.
- **Analyze Colors**: Extract dominant and complementary colors to enhance your images.
- **Apply Overlays**: Add transparent overlays and tint them with specified colors.
- **Save Images**: Export images in **JPEG, PNG, or WEBP**, with proper handling of transparency.

This class depends on several libraries, including `PIL`, `ColorThief`, `icrawler`, and `google-cloud-storage`.

---

## Installation

Install **ImageArtificer** directly from GitHub:

```bash
pip install git+https://github.com/south-bend-code-works/image_artificer.git
```

---

## Requirements

- Python 3.6 or higher
- Required Python libraries:
    - `Pillow`
    - `Matplotlib`
    - `colorthief`
    - `icrawler`
    - `google-cloud-storage`
    - `pillow-heif`

Install dependencies using:

```bash
pip install -r requirements.txt
```

---

## Usage

### Basic Example
```python
from image_artificer import ImageArtificer

# Load an image from local disk
img_art = ImageArtificer.from_local_disk("example.png")

# Resize with padding
resized_img = img_art.resize_and_pad_image(size=(800, 800), padding_color="dominant")

# Apply an overlay
resized_img.apply_overlay("overlay.png", color="#FF5733")

# Save as PNG
resized_img.save_to_local("output_image.png", format="PNG")
```

### Fetch from Web
```python
img_art = ImageArtificer.from_url("https://example.com/sample.jpg")
img_art.save_to_local("downloaded.png", format="PNG")
```

### Save to Google Cloud Storage
```python
from google.cloud import storage

gcs_client = storage.Client()
img_art.save_to_gcs(gcs_client, "my-bucket", "folder/output.webp", format="WEBP")
```

---

## Supported Image Formats
| Operation    | JPEG | PNG  | WEBP |
|-------------|------|------|------|
| Load        | ✅   | ✅   | ✅   |
| Resize      | ✅   | ✅   | ✅   |
| Transparency| ❌   | ✅   | ✅   |
| Save        | ✅   | ✅   | ✅   |

- **JPEG**: No transparency (converts RGBA to RGB).
- **PNG & WEBP**: Transparency is fully supported.

---

## License
This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

---

## Contributing
We welcome contributions! Feel free to:
- Open an issue for bugs or feature requests.
- Submit a pull request for improvements.

🚀 Happy coding with `ImageArtificer`!
