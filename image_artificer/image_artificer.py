import os
from PIL import Image
import matplotlib.pyplot as plt
from colorthief import ColorThief
import colorsys
import tempfile
from icrawler.builtin import GoogleImageCrawler

from pillow_heif import register_heif_opener
# Register HEIF/HEIC support for Pillow
register_heif_opener()

class ImageArtificer:

    ###################
    # Constructor
    ###################

    def __init__(self, img=None, storage_provider=None, storage_credentials=None):
        """
        Initialize the ImageArtificer instance based on the provided PIL image.

        :param img: The PIL image object.
        :storage_provider (str, optional): The storage provider ('local', 'gcs', 's3', 'azure', 'gdrive').
        :storage_credentials (dict, optional): Credentials or client for storage provider authentication.
        """

        self._img = img.convert('RGBA')  # Ensure the image has an alpha channel
        self.storage_handler = None

        # Setup the storage provider, if applicable
        if storage_provider:
            self.set_storage_provider(storage_provider, **storage_credentials)

        # Find the dominant and complementary colors for the img
        # Write the PIL image to a temporary file and pass it to ColorThief
        with tempfile.NamedTemporaryFile(delete=True, suffix=".png") as temp_file:
            # Save the image to the temporary file in PNG format
            self._img.save(temp_file, format='PNG')
            temp_file.flush()  # Ensure the file is written to disk

            # Initialize ColorThief with the temporary file's path
            color_thief = ColorThief(temp_file.name)
            self._dominant_color = color_thief.get_color(quality=1)
            self._comp_color = self.calculate_complementary_color(self.dominant_color)

    ###################
    # Properties
    ###################

    @property
    def dominant_color(self):
        """Getter for dominant color; no setter, making it read-only"""
        return self._dominant_color

    @property
    def complementary_color(self):
        """Getter for complementary color; no setter, making it read-only"""
        return self._comp_color

    ###################
    # Class Methods
    ###################

    @classmethod
    def from_local_disk(cls, file_path):
        """
        Create an ImageArtificer instance from an image on the local disk.

        :param file_path: Path to the image file on the local disk.

        Returns:
        - ImageArtificer: An instance of the ImageArtificer class initialized with the image from disk.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"The file at {file_path} does not exist.")

        img = Image.open(file_path)
        return cls(img=img)

    @classmethod
    def from_google_cloud_storage(cls, storage_client, bucket_name, file_path):
        """
        Create an ImageArtificer instance from an image stored in Google Cloud Storage.

        This method downloads an temporary image file from a specified Google Cloud Storage bucket and
        initializes an ImageArtificer instance.

        Parameters:
        - storage_client: The Google Cloud Storage client used to access the storage.
        - bucket_name (str): The name of the bucket where the image is stored.
        - folder_path (str): The path to the folder within the bucket that contains the image.
        - file_name (str): The name of the image file to download.

        Returns:
        - ImageArtificer: An instance of the ImageArtificer class initialized with the downloaded image.
        """

        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(file_path)

        with tempfile.NamedTemporaryFile(delete=True, suffix=".tmp") as temp_file:
            blob.download_to_filename(temp_file.name)
            img = Image.open(temp_file.name)

        return cls(img=img)

    @classmethod
    def from_google_search(cls, search_keyword, license=None):
        """
        Create an ImageArtificer instance from a Google image search result.

        License:
        - “noncommercial” (labeled for noncommercial reuse)
        - “commercial” (labeled for reuse)
        - “noncommercial,modify” (labeled for noncommercial reuse with modification)
        - “commercial,modify” (labeled for reuse with modification)

        Parameters:
        - search_keyword (str): The keyword to search for images.
        - save_file_name (str): The name of the file to save the downloaded image as. Defaults to '0'.
        - license (str, optional): The license type to filter the image search. Defaults to None.

        Returns:
        - ImageArtificer: An instance of the ImageArtificer class initialized with the downloaded image.
        """
        # Create a temporary directory using tempfile, all contents are deleted after the with block
        with tempfile.TemporaryDirectory() as temp_folder:
            import logging
            google_crawler = GoogleImageCrawler(storage={'root_dir': temp_folder})
            google_crawler.set_logger(logging.critical)
            # Set up filters if a license is provided
            filters = {'license': license} if license else None
            google_crawler.crawl(keyword=search_keyword, max_num=1, filters=filters)

            files = os.listdir(temp_folder)
            files = [f for f in files if os.path.isfile(os.path.join(temp_folder, f))]

            if not files:
                raise FileNotFoundError("No image found in search results")

            first_file_name = files[0]

            # Open and return the image after the temp directory is cleaned up
            img = Image.open(os.path.join(temp_folder, first_file_name))

        return cls(img=img)

    @classmethod
    def from_url(cls, url):
        """
        Create an ImageArtificer instance from an image URL.

        Parameters:
        - url (str): The URL of the image to be downloaded.

        Returns:
        - ImageArtificer: An instance of the ImageArtificer class initialized with the downloaded image.

        Raises:
        - Exception: If the image cannot be downloaded (HTTP status code is not 200).

        Notes:
        - The downloaded image is temporarily stored in a named temporary file with a .jpg suffix.
        - The temporary file will be automatically deleted when closed.
        """
        import requests
        response = requests.get(url)
        if response.status_code == 200:
            with tempfile.NamedTemporaryFile(delete=True, suffix=".jpg") as temp_file:
                with open(temp_file.name, 'wb') as f:
                    f.write(response.content)
                img = Image.open(temp_file.name)
            return cls(img=img)
        else:
            raise Exception("Failed to download image from URL")

    ###################
    # Static Methods
    ###################

    @staticmethod
    def calculate_complementary_color(color):
        """
        Calculate the complementary color of the given RGB color.

        Parameters:
        - color (tuple): A tuple of three integers representing the RGB color,
        where each integer is in the range [0, 255].

        Returns:
        - tuple: A tuple of three integers representing the complementary RGB color,
        where each integer is in the range [0, 255].

        Raises:
        - ValueError: If the input color is not a tuple of three integers
        within the valid range.

        Notes:
        - The complementary color is calculated using the HSV color model by shifting
        the hue by 180 degrees.
        """
        if not (isinstance(color, tuple) and len(color) == 3 and all(0 <= c <= 255 for c in color)):
            raise ValueError("Color must be a tuple of three integers between 0 and 255.")
        r, g, b = [x / 255.0 for x in color]
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        h = (h + 0.5) % 1.0
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        return tuple(int(x * 255) for x in (r, g, b))

    ###################
    # Instance Methods
    ###################

    def resize_and_pad_image(self, size=(800, 800), padding_color="dominant", inplace=False):
        """
        Resize the image to fit within the specified size and pad it with a dominant
        or complementary color.

        Parameters:
        - size (tuple, optional): A tuple representing the target size (width, height)
          in pixels. Defaults to (800, 800).
        - padding_color (str or tuple, optional): Determines the background color to pad
          the image with. It can be 'dominant', 'complementary', or a tuple (R, G, B) for
          a specific color. Defaults to 'dominant'.
        - inplace (bool, optional): Whether to modify the image in place. Defaults to False.

        Returns:
        - ImageArtificer: The instance of the class, or a new instance if inplace=False.

        Notes:
        - The method maintains the original aspect ratio of the image while resizing.
        - If the image has transparency, it is centered on a fully white background.
        - If the image does not have transparency, it is centered on a background colored
          with either the dominant color or the complementary color, depending on the
          value of `self._padding_color_method`.
        - The resulting image is converted to RGB to ensure compatibility with JPEG format.
        """
        img = self._img

        # Calculate aspect ratios
        original_aspect_ratio = img.width / img.height
        target_aspect_ratio = size[0] / size[1]

        # Determine new size based on aspect ratio
        if original_aspect_ratio > target_aspect_ratio:
            # Image is wider than the target size
            new_width = size[0]
            new_height = int(size[0] / original_aspect_ratio)
        else:
            # Image is taller or the same aspect ratio as the target size
            new_height = size[1]
            new_width = int(size[1] * original_aspect_ratio)

        # Resize image while maintaining aspect ratio
        img = img.resize((new_width, new_height), Image.LANCZOS)

        # Determine if image has transparency already
        has_transparency = False
        if img.mode == 'RGBA':
            # Extract alpha channel and check for any transparency
            alpha_channel = img.split()[-1]  # Alpha channel is the last one in RGBA
            if any(pixel < 255 for pixel in alpha_channel.getdata()):
                has_transparency = True

        # Center the image in our new size
        img_w, img_h = img.size
        offset = ((size[0] - img_w) // 2, (size[1] - img_h) // 2)

        # Create new image with transparent background (RGBA) or padding color if no transparency
        if has_transparency:
            # Fully white background
            background_img = Image.new("RGBA", size, (255, 255, 255, 255))
        else:
            # Determine background_color from padding_color argument
            if isinstance(padding_color, str):
                if padding_color == 'dominant':
                    background_color = self._dominant_color
                elif padding_color == 'complementary':
                    background_color = self._comp_color
                else:
                    raise ValueError("Invalid padding color method. Use 'dominant' or 'complementary'.")
            elif isinstance(padding_color, tuple) and len(padding_color) == 3:
                if all(isinstance(value, int) and 0 <= value <= 255 for value in padding_color):
                    background_color = padding_color
                else:
                    raise ValueError("Invalid padding color provided.")

            # Solid color background
            background_img = Image.new("RGBA", size, background_color + (255,))

        # Paste the image onto the new background
        background_img.paste(img, offset, img)  # Use the image itself as a mask to preserve transparency

        if inplace:
            # If inplace is True, modify the original image and return self
            self._img = background_img
            return self
        else:
            # If inplace is False, return a new ImageArtificer instance with the new image
            new_instance = ImageArtificer(background_img)  # Create a new instance
            return new_instance

    def apply_overlay(self, file_path, color=None):
        """
        Apply an overlay image on top of an existing base image, optionally tinting the overlay with a provided color.

        Args:
            file_path (str): Path to the overlay image file (PNG with transparency).
            color (str or tuple, optional): The tint color to apply to the overlay.
                Can be provided as a hex string (e.g., '#FF5733') or an RGB tuple (e.g., (255, 87, 51)).
                If no color is provided, the overlay is applied without tinting.

        Returns:
            self: The instance of the class, allowing for method chaining.

        Notes:
            - The overlay image is resized to match the dimensions of the base image if necessary.
            - If a tint color is provided, the overlay is converted to grayscale to preserve shading while applying the new color.
            - The original alpha channel from the overlay is maintained during tinting.
            - The final image is converted to RGB format to ensure compatibility with JPG export.
        """
        # 1. Read in overlay image from disk and ensure it has an alpha channel
        overlay = Image.open(file_path).convert("RGBA")

        # 2. Ensure overlay image dimensions are equal to our base image
        target_width = self._img.width
        target_height = self._img.height

        # 3. Resize overlay if necessary
        if overlay.size != (target_width, target_height):
            overlay = overlay.resize((target_width, target_height), Image.LANCZOS)

        # 4. If color was provided, apply tint
        if color:
            if isinstance(color, str):  # If hex color is provided
                # Convert hex color to RGB
                color = color.lstrip('#')
                target_color = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
            elif isinstance(color, tuple) and len(color) == 3:  # If RGB tuple is provided
                target_color = color
            else:
                raise ValueError("Color must be a hex string or an RGB tuple")

            # Convert the overlay to grayscale to get luminance
            grayscale_overlay = overlay.convert("L")

            # Create a solid color image using the target color
            color_overlay = Image.new("RGB", overlay.size, target_color)

            # Apply the luminance of the grayscale image to the color overlay
            # This step preserves shading while applying the new color
            tinted_overlay = Image.composite(color_overlay, overlay.convert("RGB"), grayscale_overlay)

            # Restore the original alpha channel from the RGBA image
            tinted_overlay.putalpha(overlay.split()[3])

            overlay = tinted_overlay

        # 6. Paste the overlay on top of _img
        self._img.paste(overlay, (0, 0), overlay)

        return self

    def save_to_local(self, file_path, format="JPEG"):
        """
        Save the image to the local filesystem.

        Args:
            file_path (str): The path to save the image.
            format: Should be JPEG, PNG, or WEBP

        Returns:
            None: The method does not return a value.
        Notes:
             - The method checks if the image is in RGBA mode (has an alpha channel).
             If so, it converts the image to RGB, dropping the alpha channel,
             since JPEG format does not support transparency.
        """

        img = self._img

        if format.upper() == "JPEG":
            # Check if the image has an alpha channel
            if img.mode == 'RGBA':
                print("JPEG can't be saved with Alpha Channel; converting to RGB.")
                img = img.convert('RGB')

        # Save the image in the specified format
        img.save(file_path, format=format.upper())

        print(f"File saved to local directory: {file_path}")


    def save_to_gcs(self, client, bucket_name, file_path, format="JPEG"):
        """
        Save the resized and padded image to Google Cloud Storage

        Args:
            client: Authenticated Google Cloud Storage client.
            bucket_name (str): The name of the GCS bucket.
            file_path (str): The path to save the image.
            format (str): Should be JPEG, PNG, or WEBP

        Returns:
            None: The method does not return a value.
        """

        bucket = client.get_bucket(bucket_name)

        if format == "JPEG":
            suffix = ".jpg"
        else:
            suffix = "." + format

        # Create a temporary file path
        with tempfile.NamedTemporaryFile(delete=True, suffix=suffix) as temp_file:
            temp_image_path = temp_file.name

            img = self._img
            # Can't have Alpha if saving to JPEG
            if format == "JPEG":
                if img.mode == 'RGBA':
                    # Convert to RGB, dropping the alpha channel
                    img = img.convert('RGB')

            img.save(temp_image_path, format=format)

            blob = bucket.blob(file_path)
            blob.upload_from_filename(temp_image_path)

    ###################
    # String representation
    ###################

    def __repr__(self):
        """
        Return a string representation of the ImageArtificer instance.

        This method displays the image using Matplotlib, turning off the axis, and shows
        the image on the screen. It then constructs a string representation that includes
        information about the dominant and complementary colors of the image, as well as
        the image path and the padding color method used.

        Returns:
            str: A formatted string containing the dominant color,
                complementary color, and details of the ImageArtificer instance.

        Notes:
            - The dominant and complementary colors are displayed in their respective ANSI
            color codes for better visibility in terminals that support it.
            - The image is shown using Matplotlib, which requires a suitable environment
            for displaying plots.
        """
        plt.imshow(self._img)
        plt.axis('off')
        plt.show()
        image_size = self._img.size
        dominant_rgb = self._dominant_color
        complementary_rgb = self._comp_color

        def rgb_to_ansi(r, g, b):
            return f"\033[38;2;{r};{g};{b}m"

        dominant_color_code = rgb_to_ansi(*dominant_rgb)
        complementary_color_code = rgb_to_ansi(*complementary_rgb)
        reset_color_code = "\033[0m"

        repr_str = (f"{dominant_color_code}Dominant color: RGB{dominant_rgb}{reset_color_code}\n"
                    f"{complementary_color_code}Complementary color: RGB{complementary_rgb}{reset_color_code}\n"
                    f"image_size={image_size})")
        return repr_str