# NJ Image Tools for Blender

NJ Image Tools is a Blender addon designed to enhance texture management within Blender, particularly focusing on DirectDraw Surface (DDS) format operations. It provides functionalities for converting images to DDS format using TexConv, fixing mipmaps for DDS textures, and resizing images directly within Blender.

## Features

- **Convert Images to DDS**: Utilize TexConv to convert images to DDS format with various compression options.
- **Fix Mip Maps**: Correct mipmaps for individual DDS images or all DDS textures within a folder.
- **Resize Images**: Resize images using Pillow, supporting a range of preset and custom sizes. (Note: .dds file resizing is not supported)
- **Compression Format Selection**: Choose from a variety of compression formats for DDS conversion, including BC1_UNORM (DXT1), BC2_UNORM (DXT3), BC3_UNORM (DXT5), and more.
- **Folder Operations**: Perform mip map fixing on all DDS textures within a selected folder.

## Installation

1. Ensure Blender 4.0.0 or newer is installed on your system.
2. Download the NJ Image Tools addon.
3. extract contents and then zip the nj_image_tools folder
4. Open Blender and go to `Edit > Preferences > Add-ons`.
5. Click `Install` and navigate to the downloaded addon file.
6. Enable the addon by checking the box next to its name.

## Usage

After installation, the addon's functionalities can be accessed from the `Properties > Material` tab.

### Convert to DDS

1. Select the object with the texture you wish to convert.
2. In the `NJ-TexConv` panel, select the desired compression format.
3. Click `Convert` to convert the image textures of the selected object to DDS format.

### Fix Mip Maps

1. Select the object with the DDS texture(s) you wish to fix mipmaps for.
2. Click `Fix Mip Maps` to correct the mipmaps of the DDS textures.

### Resize Images

1. Select the object with the image textures you wish to resize.
2. In the `NJ-Resize Images` panel, choose a preset size or enter a custom size.
3. Click `Resize Images` to resize the image textures of the selected object.

## Dependencies

- Blender 4.0.0 or newer
- Pillow (automatically installed by the addon if not present)

## Contributing

Contributions to NJ Image Tools are welcome! Please feel free to submit pull requests or report issues on the GitHub repository.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Nomadic Jester, for the initial creation and maintenance of the addon.
- The Blender community, for their invaluable resources and support.
